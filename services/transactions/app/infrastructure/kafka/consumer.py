import asyncio
import json
import logging
from pathlib import Path

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


async def consume_classified_loop(db_session_maker) -> None:
    consumer = AIOKafkaConsumer(
        settings.KAFKA.KAFKA_TOPIC_TRANSACTION_CLASSIFIED,
        settings.KAFKA.KAFKA_TOPIC_TRANSACTION_UPDATED,
        bootstrap_servers=settings.KAFKA.KAFKA_BOOTSTRAP_SERVERS,
        group_id=settings.KAFKA.KAFKA_GROUP_ID,
        enable_auto_commit=False,
        auto_offset_reset="earliest",
    )

    health_task: asyncio.Task | None = None
    started = False

    try:
        await consumer.start()
        started = True
        health_task = asyncio.create_task(keep_alive_task())
        logger.info(
            "Kafka transactions consumer started for topics: %s, %s",
            settings.KAFKA.KAFKA_TOPIC_TRANSACTION_CLASSIFIED,
            settings.KAFKA.KAFKA_TOPIC_TRANSACTION_UPDATED,
        )

        async for message in consumer:
            req_id: str | None = None
            if message.headers:
                for key, value in message.headers:
                    if key == "X-Request-ID":
                        req_id = value.decode("utf-8")
                        break

            set_request_id(req_id)

            try:
                payload = json.loads(message.value)
                event = TransactionClassifiedMessage.model_validate(payload)
                async with UnitOfWork(db_session_maker) as uow:
                    service = TransactionService(uow)
                    await service.apply_classification(
                        event.transaction_id,
                        event.category_id,
                    )
                await consumer.commit()
            except Exception as exc:
                logger.error(
                    "Failed to process transaction category message at offset %s: %s",
                    message.offset,
                    exc,
                    exc_info=True,
                )

    except asyncio.CancelledError:
        logger.info("Kafka transactions consumer cancelled")
        raise
    except Exception as exc:
        logger.error("Kafka transactions consumer stopped: %s", exc, exc_info=True)
    finally:
        if health_task:
            health_task.cancel()
        if started:
            await consumer.stop()
