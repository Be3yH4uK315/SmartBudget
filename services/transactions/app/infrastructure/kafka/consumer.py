import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from aiokafka import AIOKafkaConsumer
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.context import set_request_id
from app.domain.schemas.kafka import (
    TransactionCategoryUpdatedMessage,
    TransactionClassifiedMessage,
)
from app.infrastructure.db.uow import UnitOfWork
from app.services.service import TransactionService

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


class KafkaConsumerWorker:
    """Kafka consumer для применения классификации транзакций."""

    def __init__(self, db_session_maker: Any) -> None:
        self.db_session_maker = db_session_maker
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

                for _, messages in batches.items():
                    if not messages:
                        continue

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
            event = self._parse_event(
                topic=message.topic,
                payload=payload,
            )
            await self.process_event(event)

            logger.info(
                "Kafka message processed",
                extra={
                    "topic": message.topic,
                    "offset": message.offset,
                },
            )

        except (json.JSONDecodeError, ValidationError):
            logger.exception(
                "Kafka message validation failed",
                extra={
                    "topic": message.topic,
                    "offset": message.offset,
                },
            )
            raise

        except SQLAlchemyError:
            logger.exception(
                "Kafka message processing failed with database error",
                extra={
                    "topic": message.topic,
                    "offset": message.offset,
                },
            )
            raise

        except Exception:
            logger.exception(
                "Kafka message processing failed with transient error",
                extra={
                    "topic": message.topic,
                    "offset": message.offset,
                },
            )
            raise

    async def process_event(
        self,
        event: TransactionClassifiedMessage | TransactionCategoryUpdatedMessage,
    ) -> None:
        """Применяет категорию из Kafka event к транзакции."""
        async with UnitOfWork(self.db_session_maker) as uow:
            service = TransactionService(uow)
            await service.apply_classification(
                user_id=event.user_id,
                transaction_id=event.transaction_id,
                category_id=self._extract_category_id(event),
            )

    def _parse_event(
        self,
        topic: str,
        payload: dict[str, Any],
    ) -> TransactionClassifiedMessage | TransactionCategoryUpdatedMessage:
        """Парсит Kafka payload по topic."""
        event_payload = payload.get("payload", payload)

        if topic == settings.KAFKA.KAFKA_TOPIC_TRANSACTION_CATEGORY_UPDATED:
            return TransactionCategoryUpdatedMessage.model_validate(event_payload)

        if topic == settings.KAFKA.KAFKA_TOPIC_TRANSACTION_CLASSIFIED:
            return TransactionClassifiedMessage.model_validate(event_payload)

        raise ValueError(f"Unknown Kafka topic for transactions service: {topic}")

    @staticmethod
    def _extract_category_id(
        event: TransactionClassifiedMessage | TransactionCategoryUpdatedMessage,
    ) -> int:
        """Возвращает новую категорию из event."""
        if isinstance(event, TransactionClassifiedMessage):
            return event.category_id

        return event.new_category_id


async def consume_classified_loop(db_session_maker: Any) -> None:
    """Запускает consumer loop для classified/category_updated events."""
    worker = KafkaConsumerWorker(db_session_maker)
    await worker.run()
