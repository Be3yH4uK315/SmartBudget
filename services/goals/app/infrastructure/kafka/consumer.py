import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from aiokafka import AIOKafkaConsumer

from app.core import metrics
from app.core.config import settings
from app.core.context import set_request_id
from app.domain.schemas import kafka as schemas
from app.infrastructure.db.uow import UnitOfWork
from app.infrastructure.kafka.producer import KafkaProducerWrapper
from app.services.service import GoalService

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
    """Класс для потребления сообщений из Kafka и обработки событий транзакций для целей."""

    def __init__(
        self,
        db_session_maker: Any,
        dlq_producer: KafkaProducerWrapper,
    ) -> None:
        self.db_session_maker = db_session_maker
        self.dlq_producer = dlq_producer
        self.consumer: AIOKafkaConsumer | None = None
        self.health_task: asyncio.Task | None = None

    @property
    def topic(self) -> str:
        return settings.KAFKA.consumer_topic

    @property
    def topics(self) -> tuple[str, str]:
        return settings.KAFKA.consumer_topics

    @property
    def group_id(self) -> str:
        return settings.KAFKA.consumer_group_id

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

                for topic_partition, messages in batches.items():
                    if not messages:
                        continue

                    highwater = self.consumer.highwater(topic_partition)
                    if highwater is not None:
                        current_offset = messages[-1].offset + 1
                        metrics.KAFKA_CONSUMER_LAG.labels(
                            topic=topic_partition.topic,
                            partition=topic_partition.partition,
                        ).set(highwater - current_offset)

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
        async with UnitOfWork(self.db_session_maker) as uow:
            await uow.goals.ensure_current_partition()

        service = GoalService(UnitOfWork(self.db_session_maker))
        for message in messages:
            await self.handle_message(message, service)

    async def handle_message(self, message: Any, service: GoalService) -> None:
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
            if message.topic == settings.KAFKA.KAFKA_TOPIC_TRANSACTION_DELETED:
                event = schemas.TransactionDeletedEvent.model_validate(payload)
                await self.process_deleted_event(event, service)
            else:
                event = schemas.TransactionEvent.model_validate(payload)
                await self.process_event(event, service)
            logger.info(
                "Kafka message processed",
                extra={"topic": message.topic, "offset": message.offset},
            )
        except Exception as exc:
            logger.exception(
                "Kafka message processing failed",
                extra={"topic": message.topic, "offset": message.offset},
            )
            metrics.KAFKA_DLQ_ERRORS.labels(
                topic=message.topic,
                reason=type(exc).__name__,
            ).inc()
            await self.send_to_dlq(message, exc, request_id)

    async def process_event(
        self,
        event: schemas.TransactionEvent,
        service: GoalService,
    ) -> None:
        await service.update_goal_balance(event)

    async def process_deleted_event(
        self,
        event: schemas.TransactionDeletedEvent,
        service: GoalService,
    ) -> None:
        await service.rollback_goal_transaction(event)

    async def send_to_dlq(
        self,
        message: Any,
        exc: Exception,
        request_id: str | None,
    ) -> None:
        headers = [("error", str(exc).encode("utf-8"))]
        if request_id:
            headers.append(("X-Request-ID", request_id.encode("utf-8")))

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
                extra={"topic": message.topic, "offset": message.offset},
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


async def consume_loop(
    db_session_maker: Any,
    dlq_producer: KafkaProducerWrapper,
) -> None:
    worker = KafkaConsumerWorker(db_session_maker, dlq_producer)
    await worker.run()
