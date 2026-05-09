import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from aiokafka import AIOKafkaConsumer

from app.core import metrics
from app.core.config import settings
from app.core.context import set_request_id
from app.domain.schemas import kafka as schemas
from app.infrastructure.db.uow import UnitOfWork
from app.infrastructure.kafka.producer import KafkaProducerWrapper
from app.services.service import NotificationService

logger = logging.getLogger(__name__)

HEALTH_FILE = Path("/tmp/healthy")
KEEP_ALIVE_INTERVAL_SECONDS = 5
CONSUMER_TIMEOUT_MS = 1000
REQUEST_ID_HEADER = "X-Request-ID"


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


def _event_id_from_message(message: Any) -> Any:
    """Создает детерминированный event_id для auth outbox message."""
    return uuid5(
        NAMESPACE_URL,
        f"{message.topic}:{message.partition}:{message.offset}",
    )


def _timestamp_from_message(message: Any) -> datetime:
    """Возвращает timestamp Kafka-сообщения как UTC datetime."""
    if not message.timestamp:
        return datetime.now(timezone.utc)

    return datetime.fromtimestamp(
        message.timestamp / 1000,
        tz=timezone.utc,
    )


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
    def topics(self) -> tuple[str, str]:
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
                extra={
                    "topics": self.topics,
                    "group_id": self.group_id,
                },
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

                    for message in messages:
                        await self.handle_message(message)

                if batches and not settings.KAFKA.KAFKA_ENABLE_AUTO_COMMIT:
                    await self.consumer.commit()

        except asyncio.CancelledError:
            logger.info(
                "Kafka worker shutdown requested",
                extra={
                    "topics": self.topics,
                    "group_id": self.group_id,
                },
            )
            raise

        except Exception:
            logger.exception(
                "Kafka worker failed",
                extra={
                    "topics": self.topics,
                    "group_id": self.group_id,
                },
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
                extra={
                    "topics": self.topics,
                    "group_id": self.group_id,
                },
            )

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
            payload = json.loads(message.value)

            service = NotificationService(
                UnitOfWork(self.db_session_maker),
                self.arq_pool,
            )

            await self.process_event(payload, message, service)

            logger.info(
                "Kafka message processed",
                extra={
                    "topic": message.topic,
                    "offset": message.offset,
                },
            )

        except Exception as exc:
            await self._handle_processing_error(
                message=message,
                exc=exc,
                request_id=request_id,
            )

    async def process_event(
        self,
        payload: dict[str, Any],
        message: Any,
        service: NotificationService,
    ) -> None:
        """Маршрутизирует Kafka payload в нужный обработчик сервиса."""
        if message.topic == settings.KAFKA.KAFKA_TOPIC_AUTH:
            event = schemas.AuthOutboxEvent.model_validate(payload)
            await service.process_auth_outbox_event(
                event=event,
                event_id=_event_id_from_message(message),
                timestamp=_timestamp_from_message(message),
            )
            return

        event = schemas.IncomingNotificationEvent.model_validate(payload)
        await service.process_incoming_event(event)

    async def send_to_dlq(
        self,
        message: Any,
        exc: Exception,
        request_id: str | None,
    ) -> None:
        """Публикует проблемное сообщение в DLQ."""
        headers = [("error", str(exc).encode("utf-8"))]

        if request_id:
            headers.append((REQUEST_ID_HEADER, request_id.encode("utf-8")))

        success = await self.dlq_producer.send_event(
            topic=settings.KAFKA.dlq_topic,
            value=message.value,
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
            extra={
                "topic": message.topic,
                "offset": message.offset,
            },
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
