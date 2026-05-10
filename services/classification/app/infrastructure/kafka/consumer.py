import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from aiokafka import AIOKafkaConsumer
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.domain.schemas.kafka import TransactionNeedCategoryEvent
from app.infrastructure.db.uow import UnitOfWork
from app.infrastructure.kafka.producer import KafkaProducerWrapper
from app.services.classification.rules import ruleManager
from app.services.classification.service import ClassificationService
from app.services.ml.manager import modelManager

logger = logging.getLogger(__name__)

HEALTH_FILE = Path("/tmp/healthy")
KEEP_ALIVE_INTERVAL_SECONDS = 5
CONSUMER_TIMEOUT_MS = 1000
REQUEST_ID_HEADER = "X-Request-ID"
ERROR_HEADER = "error"


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


def _event_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Возвращает бизнес-payload из envelope или старого Kafka payload."""
    nested_payload = payload.get("payload")

    if isinstance(nested_payload, dict):
        return nested_payload

    return payload


class KafkaConsumerWorker:
    """Kafka consumer классификации транзакций с отправкой ошибок в DLQ."""

    def __init__(
        self,
        redis_client: Any,
        db_session_maker: Any,
        dlq_producer: KafkaProducerWrapper,
    ) -> None:
        self.redis_client = redis_client
        self.db_session_maker = db_session_maker
        self.dlq_producer = dlq_producer
        self.consumer: AIOKafkaConsumer | None = None
        self.health_task: asyncio.Task | None = None

    @property
    def topic(self) -> str:
        """Возвращает topic, который читает consumer."""
        return settings.KAFKA.consumer_topic

    @property
    def group_id(self) -> str:
        """Возвращает group id consumer-а."""
        return settings.KAFKA.consumer_group_id

    def _build_consumer(self) -> AIOKafkaConsumer:
        """Создает AIOKafkaConsumer."""
        return AIOKafkaConsumer(
            self.topic,
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
                    "topic": self.topic,
                    "group_id": self.group_id,
                },
            )

            while True:
                await self._refresh_runtime_dependencies()

                batches = await self.consumer.getmany(
                    timeout_ms=CONSUMER_TIMEOUT_MS,
                    max_records=settings.KAFKA.KAFKA_BATCH_SIZE,
                )

                for _, messages in batches.items():
                    if not messages:
                        continue

                    await self.process_batch(messages)

                if batches and not settings.KAFKA.KAFKA_ENABLE_AUTO_COMMIT:
                    await self.consumer.commit()

        except asyncio.CancelledError:
            logger.info(
                "Kafka worker shutdown requested",
                extra={
                    "topic": self.topic,
                    "group_id": self.group_id,
                },
            )
            raise

        except Exception:
            logger.exception(
                "Kafka worker failed",
                extra={
                    "topic": self.topic,
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
                    "topic": self.topic,
                    "group_id": self.group_id,
                },
            )

    async def process_batch(self, messages: list[Any]) -> None:
        """Обрабатывает batch Kafka-сообщений."""
        pipeline = modelManager.get_pipeline()
        rules = ruleManager.get_rules()

        async with UnitOfWork(self.db_session_maker) as uow:
            service = ClassificationService(
                uow=uow,
                redis=self.redis_client,
                ml_pipeline=pipeline,
                rules=rules,
            )

            for message in messages:
                await self.handle_message(
                    message=message,
                    service=service,
                    uow=uow,
                )

            await uow.commit()

    async def handle_message(
        self,
        message: Any,
        service: ClassificationService,
        uow: UnitOfWork,
    ) -> None:
        """Обрабатывает одно Kafka-сообщение внутри savepoint."""
        logger.info(
            "Kafka message received",
            extra={
                "topic": message.topic,
                "partition": message.partition,
                "offset": message.offset,
            },
        )

        request_id = _request_id_from_headers(message.headers)

        try:
            async with uow.make_savepoint():
                payload = json.loads(message.value)
                event_payload = _event_payload(payload)
                event = TransactionNeedCategoryEvent.model_validate(event_payload)
                await self.process_event(event, service)

            logger.info(
                "Kafka message processed",
                extra={
                    "topic": message.topic,
                    "offset": message.offset,
                },
            )

        except (json.JSONDecodeError, ValidationError) as exc:
            logger.exception(
                "Kafka message validation failed",
                extra={
                    "topic": message.topic,
                    "offset": message.offset,
                },
            )
            await self.send_to_dlq(message, exc, request_id)

        except SQLAlchemyError as exc:
            logger.exception(
                "Kafka message processing failed with database error",
                extra={
                    "topic": message.topic,
                    "offset": message.offset,
                },
            )
            await self.send_to_dlq(message, exc, request_id)

        except Exception as exc:
            logger.exception(
                "Kafka message processing failed with transient error",
                extra={
                    "topic": message.topic,
                    "offset": message.offset,
                },
            )
            await self.send_to_dlq(message, exc, request_id)

    async def process_event(
        self,
        event: TransactionNeedCategoryEvent,
        service: ClassificationService,
    ) -> None:
        """Передает событие в ClassificationService."""
        await service.classify_transaction(event)

    async def send_to_dlq(
        self,
        message: Any,
        exc: Exception,
        request_id: str | None,
    ) -> None:
        """Отправляет проблемное сообщение в DLQ."""
        headers = [
            (ERROR_HEADER, str(exc).encode("utf-8")),
        ]
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

    async def _refresh_runtime_dependencies(self) -> None:
        """Обновляет ML-модель и правила перед чтением batch."""
        await modelManager.check_for_updates(self.db_session_maker)
        await ruleManager.check_for_updates(self.db_session_maker)


async def consume_loop(
    redis_client: Any,
    db_session_maker: Any,
    dlq_producer: KafkaProducerWrapper,
) -> None:
    """Запускает consumer loop."""
    worker = KafkaConsumerWorker(
        redis_client=redis_client,
        db_session_maker=db_session_maker,
        dlq_producer=dlq_producer,
    )
    await worker.run()
