import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from aiokafka import AIOKafkaConsumer

from app.core.config import settings
from app.core.context import set_request_id
from app.domain.schemas.kafka import TransactionClassifiedMessage
from app.infrastructure.db.uow import UnitOfWork
from app.services.service import TransactionService

logger = logging.getLogger(__name__)
HEALTH_FILE = Path("/tmp/healthy")


async def keep_alive_task() -> None:
    while True:
        try:
            HEALTH_FILE.touch(exist_ok=True)
        except OSError:
            pass
        await asyncio.sleep(5)


def _request_id_from_headers(headers: list[tuple[str, bytes]] | None) -> str | None:
    if not headers:
        return None

    for key, value in headers:
        if key == "X-Request-ID":
            return value.decode("utf-8")
    return None


class KafkaConsumerWorker:
    """Класс для потребления сообщений из Kafka и обработки событий транзакций для уведомлений."""

    def __init__(self, db_session_maker: Any) -> None:
        self.db_session_maker = db_session_maker
        self.consumer: AIOKafkaConsumer | None = None
        self.health_task: asyncio.Task | None = None

    @property
    def topics(self) -> tuple[str, str]:
        return settings.KAFKA.consumer_topics

    @property
    def group_id(self) -> str:
        return settings.KAFKA.KAFKA_GROUP_ID

    def _build_consumer(self) -> AIOKafkaConsumer:
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
                    timeout_ms=1000,
                    max_records=settings.KAFKA.KAFKA_BATCH_SIZE,
                )

                for _, messages in batches.items():
                    for message in messages:
                        await self.handle_message(message)

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

    async def handle_message(self, message: Any) -> None:
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
            event = TransactionClassifiedMessage.model_validate(payload)
            await self.process_event(event)
            logger.info(
                "Kafka message processed",
                extra={"topic": message.topic, "offset": message.offset},
            )
        except Exception:
            logger.exception(
                "Kafka message processing failed",
                extra={"topic": message.topic, "offset": message.offset},
            )
            raise

    async def process_event(self, event: TransactionClassifiedMessage) -> None:
        async with UnitOfWork(self.db_session_maker) as uow:
            service = TransactionService(uow)
            await service.apply_classification(
                event.transaction_id,
                event.category_id,
            )


async def consume_classified_loop(db_session_maker: Any) -> None:
    worker = KafkaConsumerWorker(db_session_maker)
    await worker.run()
