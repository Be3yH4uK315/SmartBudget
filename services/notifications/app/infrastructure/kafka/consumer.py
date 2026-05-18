import asyncio
import json
import logging
from pathlib import Path
from typing import Any
from uuid import UUID

from aiokafka import AIOKafkaConsumer
from pydantic import TypeAdapter, ValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.core import metrics
from app.core.config import settings
from app.core.context import clear_request_id, set_request_id
from app.domain.schemas.kafka import IncomingNotificationEvent
from app.infrastructure.db.uow import UnitOfWork
from app.infrastructure.kafka.producer import KafkaProducerWrapper
from app.services.service import NotificationService
from smartbudget_shared.events import (
    AuthEventType,
    AuthUserPayload,
    BudgetEventType,
    BudgetPayload,
    DLQPayload,
    EventEnvelope,
    GoalEventType,
    GoalPayload,
    TransactionCategoryChangedPayload,
    TransactionEventType,
    TransactionUnclassifiedFoundPayload,
    create_dlq_event,
)

logger = logging.getLogger(__name__)

HEALTH_FILE = Path("/tmp/healthy")
KEEP_ALIVE_INTERVAL_SECONDS = 5
CONSUMER_TIMEOUT_MS = 1000
REQUEST_ID_HEADER = "X-Request-ID"
ERROR_HEADER = "error"

AuthEventAdapter = TypeAdapter(EventEnvelope[AuthUserPayload])
BudgetEventAdapter = TypeAdapter(EventEnvelope[BudgetPayload])
GoalEventAdapter = TypeAdapter(EventEnvelope[GoalPayload])
TransactionUnclassifiedFoundEventAdapter = TypeAdapter(
    EventEnvelope[TransactionUnclassifiedFoundPayload],
)
TransactionCategoryChangedEventAdapter = TypeAdapter(
    EventEnvelope[TransactionCategoryChangedPayload],
)

AUTH_PROFILE_EVENTS = {
    AuthEventType.PROFILE_UPDATED.value,
    AuthEventType.EMAIL_CHANGED.value,
}

AUTH_SESSION_EVENTS = {
    AuthEventType.SESSION_REVOKED.value,
}

AUTH_NOTIFICATION_EVENTS = {
    AuthEventType.USER_REGISTERED.value,
    AuthEventType.DEVICE_NEW_LOGIN.value,
    AuthEventType.PASSWORD_CHANGED.value,
    AuthEventType.ACTIVITY_SUSPICIOUS.value,
}

BUDGET_NOTIFICATION_EVENTS = {
    BudgetEventType.BUDGET_TOTAL_THRESHOLD_REACHED.value,
    BudgetEventType.BUDGET_TOTAL_EXCEEDED.value,
    BudgetEventType.BUDGET_CATEGORY_THRESHOLD_REACHED.value,
    BudgetEventType.BUDGET_CATEGORY_EXCEEDED.value,
    BudgetEventType.BUDGET_SETTINGS_CHANGED.value,
    BudgetEventType.BUDGET_CHECK_RESULTS.value,
}

GOAL_NOTIFICATION_EVENTS = {
    GoalEventType.GOAL_CREATED.value,
    GoalEventType.GOAL_COMPLETED.value,
    GoalEventType.GOAL_EXPIRED.value,
    GoalEventType.GOAL_THRESHOLD_REACHED.value,
    GoalEventType.GOAL_DEADLINE_APPROACHING.value,
    GoalEventType.GOAL_PAYMENT_MISSED.value,
}

TRANSACTION_NOTIFICATION_EVENTS = {
    TransactionEventType.TRANSACTION_UNCLASSIFIED_FOUND.value,
    TransactionEventType.TRANSACTION_CATEGORY_CHANGED.value,
}


async def keep_alive_task() -> None:
    """Периодически обновляет health-файл consumer-процесса."""
    while True:
        try:
            HEALTH_FILE.touch(exist_ok=True)
        except OSError:
            logger.debug("Failed to touch consumer health file", exc_info=True)

        await asyncio.sleep(KEEP_ALIVE_INTERVAL_SECONDS)


def _request_id_from_headers(headers: list[tuple[str, bytes]] | None) -> str | None:
    """Извлекает X-Request-ID из Kafka headers."""
    if not headers:
        return None

    for key, value in headers:
        if key == REQUEST_ID_HEADER:
            return value.decode("utf-8")

    return None


def _raw_message_value(message: Any) -> str:
    """Возвращает Kafka message value как строку."""
    if isinstance(message.value, bytes):
        return message.value.decode("utf-8")

    return str(message.value)


def _decode_message_value(message: Any) -> dict[str, Any]:
    """Декодирует Kafka message value в dict."""
    return json.loads(_raw_message_value(message))


def _decimal_to_str(value: Any) -> str | None:
    """Преобразует Decimal/числовое значение в строку для JSON props."""
    if value is None:
        return None

    return str(value)


def _uuid_to_str(value: UUID | None) -> str | None:
    """Преобразует UUID в строку для JSON props."""
    if value is None:
        return None

    return str(value)


def _compact_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Удаляет из payload поля со значением None."""
    return {key: value for key, value in payload.items() if value is not None}


def _auth_notification_payload(event: EventEnvelope[AuthUserPayload]) -> dict[str, Any]:
    """Преобразует auth event в payload уведомления."""
    return _compact_payload(
        {
            "email": event.payload.email,
            "new_email": event.payload.new_email,
            "name": event.payload.name,
            "language": event.payload.language,
            "ip": event.payload.ip,
            "device": event.payload.device,
            "location": event.payload.location,
            "reason": event.payload.reason,
            "logged_at": event.payload.logged_at.isoformat()
            if event.payload.logged_at
            else None,
            "changed_at": event.payload.changed_at.isoformat()
            if event.payload.changed_at
            else None,
            "detected_at": event.payload.detected_at.isoformat()
            if event.payload.detected_at
            else None,
        },
    )


def _budget_notification_payload(event: EventEnvelope[BudgetPayload]) -> dict[str, Any]:
    """Преобразует budget event в payload уведомления."""
    return _compact_payload(
        {
            "budget_id": _uuid_to_str(event.payload.budget_id),
            "category_id": event.payload.category_id,
            "limit_amount": _decimal_to_str(event.payload.limit_amount),
            "spent_amount": _decimal_to_str(event.payload.spent_amount),
            "percent": event.payload.percent,
            "threshold_percent": event.payload.threshold_percent,
            "checked_at": event.payload.checked_at.isoformat()
            if event.payload.checked_at
            else None,
            "total_exceeded_count": event.payload.total_exceeded_count,
            "category_exceeded_count": event.payload.category_exceeded_count,
        },
    )


def _goal_notification_payload(event: EventEnvelope[GoalPayload]) -> dict[str, Any]:
    """Преобразует goal event в payload уведомления."""
    return _compact_payload(
        {
            "goal_id": _uuid_to_str(event.payload.goal_id),
            "name": event.payload.name,
            "target_amount": _decimal_to_str(event.payload.target_amount),
            "current_amount": _decimal_to_str(event.payload.current_amount),
            "recommended_payment": _decimal_to_str(event.payload.recommended_payment),
            "progress_percent": event.payload.progress_percent,
            "current_percent": event.payload.current_percent,
            "threshold_percent": event.payload.threshold_percent,
            "days_left": event.payload.days_left,
        },
    )


def _transaction_unclassified_payload(
    event: EventEnvelope[TransactionUnclassifiedFoundPayload],
) -> dict[str, Any]:
    """Преобразует transaction.unclassified.found в payload уведомления."""
    return _compact_payload(
        {
            "amount": _decimal_to_str(event.payload.amount),
            "count": event.payload.count,
        },
    )


def _transaction_category_changed_payload(
    event: EventEnvelope[TransactionCategoryChangedPayload],
) -> dict[str, Any]:
    """Преобразует transaction.category.changed в payload уведомления."""
    return {
        "transaction_id": _uuid_to_str(event.payload.transaction_id),
        "old_category_id": event.payload.old_category_id,
        "new_category_id": event.payload.new_category_id,
    }


class KafkaConsumerWorker:
    """Kafka consumer для обработки событий notification service."""

    def __init__(
        self,
        db_session_maker: Any,
        arq_pool: Any,
        dlq_producer: KafkaProducerWrapper,
    ) -> None:
        self.db_session_maker = db_session_maker
        self.arq_pool = arq_pool
        self.dlq_producer = dlq_producer
        self.consumer: AIOKafkaConsumer | None = None
        self.health_task: asyncio.Task | None = None

    @property
    def topics(self) -> tuple[str, ...]:
        """Возвращает topics, которые читает consumer."""
        return settings.KAFKA.consumer_topics

    @property
    def group_id(self) -> str:
        """Возвращает group id consumer-а."""
        return settings.KAFKA.consumer_group_id

    def _build_consumer(self) -> AIOKafkaConsumer:
        """Создает AIOKafkaConsumer."""
        return AIOKafkaConsumer(
            *self.topics,
            bootstrap_servers=settings.KAFKA.KAFKA_BOOTSTRAP_SERVERS,
            group_id=self.group_id,
            enable_auto_commit=settings.KAFKA.KAFKA_ENABLE_AUTO_COMMIT,
            auto_offset_reset=settings.KAFKA.KAFKA_AUTO_OFFSET_RESET,
            security_protocol=settings.KAFKA.KAFKA_SECURITY_PROTOCOL,
            max_poll_records=settings.KAFKA.KAFKA_BATCH_SIZE,
        )

    async def run(self) -> None:
        """Запускает основной consumer loop."""
        self.consumer = self._build_consumer()

        try:
            await self.consumer.start()
            self.health_task = asyncio.create_task(keep_alive_task())

            logger.info(
                "Kafka worker started",
                extra={"topics": self.topics, "group_id": self.group_id},
            )

            while True:
                batches = await self.consumer.getmany(
                    timeout_ms=CONSUMER_TIMEOUT_MS,
                    max_records=settings.KAFKA.KAFKA_BATCH_SIZE,
                )

                for topic_partition, messages in batches.items():
                    if not messages:
                        continue

                    self._update_consumer_lag(topic_partition, messages)
                    await self.process_batch(messages)

                if batches and not settings.KAFKA.KAFKA_ENABLE_AUTO_COMMIT:
                    await self.consumer.commit()

        except asyncio.CancelledError:
            logger.info(
                "Kafka worker shutdown requested",
                extra={"topics": self.topics, "group_id": self.group_id},
            )
            raise

        except Exception:
            logger.exception(
                "Kafka worker failed",
                extra={"topics": self.topics, "group_id": self.group_id},
            )
            raise

        finally:
            await self.shutdown()

    async def shutdown(self) -> None:
        """Останавливает consumer и health task."""
        if self.health_task:
            self.health_task.cancel()
            try:
                await self.health_task
            except asyncio.CancelledError:
                pass

        if self.consumer:
            await self.consumer.stop()
            logger.info(
                "Kafka worker stopped",
                extra={"topics": self.topics, "group_id": self.group_id},
            )

    async def process_batch(self, messages: list[Any]) -> None:
        """Обрабатывает batch Kafka-сообщений."""
        for message in messages:
            await self.handle_message(message)

    async def handle_message(self, message: Any) -> None:
        """Обрабатывает одно Kafka-сообщение."""
        logger.info(
            "Kafka message received",
            extra={
                "topic": message.topic,
                "partition": message.partition,
                "offset": message.offset,
            },
        )

        request_id = _request_id_from_headers(message.headers)
        set_request_id(request_id)

        try:
            payload = _decode_message_value(message)

            service = NotificationService(
                UnitOfWork(self.db_session_maker),
                self.arq_pool,
            )

            await self.process_payload(payload, service)

            logger.info(
                "Kafka message processed",
                extra={"topic": message.topic, "offset": message.offset},
            )

        except (json.JSONDecodeError, ValidationError, ValueError, SQLAlchemyError) as exc:
            await self._handle_processing_error(message, exc, request_id)

        except Exception as exc:
            await self._handle_processing_error(message, exc, request_id)

        finally:
            clear_request_id()

    async def process_payload(
        self,
        payload: dict[str, Any],
        service: NotificationService,
    ) -> None:
        """Маршрутизирует Kafka envelope в нужный обработчик сервиса."""
        event_type = payload.get("event_type")

        if event_type in AUTH_PROFILE_EVENTS:
            await self._process_auth_profile_event(payload, service)
            return

        if event_type in AUTH_SESSION_EVENTS:
            await self._process_auth_session_event(payload, service)
            return

        if event_type in AUTH_NOTIFICATION_EVENTS:
            await self._process_auth_notification_event(payload, service)
            return

        if event_type in BUDGET_NOTIFICATION_EVENTS:
            await self._process_budget_notification_event(payload, service)
            return

        if event_type in GOAL_NOTIFICATION_EVENTS:
            await self._process_goal_notification_event(payload, service)
            return

        if event_type in TRANSACTION_NOTIFICATION_EVENTS:
            await self._process_transaction_notification_event(payload, service)
            return

        logger.debug("Kafka event ignored by notifications service: %s", event_type)

    async def _process_auth_profile_event(
        self,
        payload: dict[str, Any],
        service: NotificationService,
    ) -> None:
        """Обрабатывает auth events, которые только синхронизируют профиль."""
        event = AuthEventAdapter.validate_python(payload)
        await service.process_auth_event(event)

    async def _process_auth_notification_event(
        self,
        payload: dict[str, Any],
        service: NotificationService,
    ) -> None:
        """Обрабатывает auth events, которые создают уведомления."""
        event = AuthEventAdapter.validate_python(payload)
        await service.process_auth_event(event)

        await service.process_incoming_event(
            IncomingNotificationEvent(
                event_id=event.event_id,
                event_type=event.event_type,
                user_id=event.payload.user_id,
                payload=_auth_notification_payload(event),
                timestamp=event.date,
            ),
        )

    async def _process_auth_session_event(
        self,
        payload: dict[str, Any],
        service: NotificationService,
    ) -> None:
        """Обрабатывает auth events жизненного цикла сессий."""
        event = AuthEventAdapter.validate_python(payload)

        if not event.payload.session_id:
            logger.warning(
                "Session event %s ignored: session_id is missing",
                event.event_type,
            )
            return

        await service.remove_push_subscriptions_by_session(
            event.payload.user_id,
            event.payload.session_id,
        )

    async def _process_budget_notification_event(
        self,
        payload: dict[str, Any],
        service: NotificationService,
    ) -> None:
        """Обрабатывает budget events, которые создают уведомления."""
        event = BudgetEventAdapter.validate_python(payload)

        await service.process_incoming_event(
            IncomingNotificationEvent(
                event_id=event.event_id,
                event_type=event.event_type,
                user_id=event.payload.user_id,
                payload=_budget_notification_payload(event),
                timestamp=event.date,
            ),
        )

    async def _process_goal_notification_event(
        self,
        payload: dict[str, Any],
        service: NotificationService,
    ) -> None:
        """Обрабатывает goal events, которые создают уведомления."""
        event = GoalEventAdapter.validate_python(payload)

        await service.process_incoming_event(
            IncomingNotificationEvent(
                event_id=event.event_id,
                event_type=event.event_type,
                user_id=event.payload.user_id,
                payload=_goal_notification_payload(event),
                timestamp=event.date,
            ),
        )

    async def _process_transaction_notification_event(
        self,
        payload: dict[str, Any],
        service: NotificationService,
    ) -> None:
        """Обрабатывает transaction events, которые создают уведомления."""
        event_type = payload.get("event_type")

        if event_type == TransactionEventType.TRANSACTION_UNCLASSIFIED_FOUND.value:
            event = TransactionUnclassifiedFoundEventAdapter.validate_python(payload)
            await service.process_incoming_event(
                IncomingNotificationEvent(
                    event_id=event.event_id,
                    event_type=event.event_type,
                    user_id=event.payload.user_id,
                    payload=_transaction_unclassified_payload(event),
                    timestamp=event.date,
                ),
            )
            return

        if event_type == TransactionEventType.TRANSACTION_CATEGORY_CHANGED.value:
            event = TransactionCategoryChangedEventAdapter.validate_python(payload)
            await service.process_incoming_event(
                IncomingNotificationEvent(
                    event_id=event.event_id,
                    event_type=event.event_type,
                    user_id=event.payload.user_id,
                    payload=_transaction_category_changed_payload(event),
                    timestamp=event.date,
                ),
            )
            return

        logger.debug("Transaction event ignored by notifications service: %s", event_type)

    async def send_to_dlq(
        self,
        message: Any,
        exc: Exception,
        request_id: str | None,
    ) -> None:
        """Публикует проблемное сообщение в DLQ."""
        dlq_payload = DLQPayload(
            original_topic=message.topic,
            original_message=_raw_message_value(message),
            error=str(exc),
            consumer_group=self.group_id,
            retry_count=0,
        )
        dlq_event = create_dlq_event(dlq_payload)

        headers = [(ERROR_HEADER, str(exc).encode("utf-8"))]

        if request_id:
            headers.append((REQUEST_ID_HEADER, request_id.encode("utf-8")))

        success = await self.dlq_producer.send_event(
            topic=settings.KAFKA.dlq_topic,
            value=dlq_event.to_kafka_payload(),
            key=message.key,
            headers=headers,
            wait=True,
        )

        if not success:
            logger.critical(
                "Kafka DLQ publish failed",
                extra={
                    "topic": message.topic,
                    "offset": message.offset,
                    "dlq_topic": settings.KAFKA.dlq_topic,
                },
            )
            raise RuntimeError("DLQ refused message")

        logger.warning(
            "Kafka message sent to DLQ",
            extra={
                "topic": message.topic,
                "offset": message.offset,
                "dlq_topic": settings.KAFKA.dlq_topic,
            },
        )

    async def _handle_processing_error(
        self,
        message: Any,
        exc: Exception,
        request_id: str | None,
    ) -> None:
        """Обрабатывает ошибку обработки Kafka-сообщения."""
        logger.exception(
            "Kafka message processing failed",
            extra={"topic": message.topic, "offset": message.offset},
        )

        metrics.KAFKA_DLQ_ERRORS.labels(
            topic=message.topic,
            reason=type(exc).__name__,
        ).inc()

        await self.send_to_dlq(message, exc, request_id)

    def _update_consumer_lag(self, topic_partition: Any, messages: list[Any]) -> None:
        """Обновляет метрику Kafka consumer lag."""
        if not self.consumer:
            return

        highwater = self.consumer.highwater(topic_partition)
        if highwater is None:
            return

        current_offset = messages[-1].offset + 1
        metrics.KAFKA_CONSUMER_LAG.labels(
            topic=topic_partition.topic,
            partition=topic_partition.partition,
        ).set(highwater - current_offset)


async def consume_loop(
    db_session_maker: Any,
    arq_pool: Any,
    dlq_producer: KafkaProducerWrapper,
) -> None:
    """Запускает KafkaConsumerWorker."""
    worker = KafkaConsumerWorker(db_session_maker, arq_pool, dlq_producer)
    await worker.run()
