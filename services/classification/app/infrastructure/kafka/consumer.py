import asyncio
import json
import logging
from pathlib import Path
from typing import List
from aiokafka import AIOKafkaConsumer

from app.core.config import settings
from app.domain.schemas.kafka import TransactionNeedCategoryEvent
from app.infrastructure.db.uow import UnitOfWork
from app.infrastructure.kafka.producer import KafkaProducerWrapper
from app.services.classification.service import ClassificationService
from app.services.ml.manager import modelManager
from app.services.classification.rules import ruleManager

logger = logging.getLogger(__name__)
HEALTH_FILE = Path("/tmp/healthy")
BATCH_SIZE = 100

async def keep_alive_task() -> None:
    while True:
        try:
            HEALTH_FILE.touch(exist_ok=True)
        except OSError:
            pass
        await asyncio.sleep(5)

async def consume_loop(
    redis_client,
    db_session_maker,
    dlq_producer: KafkaProducerWrapper,
) -> None:
    """Основной цикл потребителя."""
    logger.info("Initializing consumer...")
    consumer = AIOKafkaConsumer(
        settings.KAFKA.TOPIC_NEED_CATEGORY,
        bootstrap_servers=settings.KAFKA.KAFKA_BOOTSTRAP_SERVERS,
        group_id=settings.KAFKA.KAFKA_GROUP_ID,
        enable_auto_commit=False,
        auto_offset_reset="latest",
        max_poll_records=BATCH_SIZE,
    )

    await consumer.start()
    logger.info("Kafka consumer started")
    health_task = asyncio.create_task(keep_alive_task())

    try:
        while True:
            await modelManager.check_for_updates(db_session_maker)
            await ruleManager.check_for_updates(db_session_maker)

            result = await consumer.getmany(
                timeout_ms=1000,
                max_records=BATCH_SIZE,
            )

            for tp, messages in result.items():
                if not messages:
                    continue

                await process_batch(
                    messages,
                    redis_client,
                    db_session_maker,
                    dlq_producer,
                )

            await consumer.commit()

    except asyncio.CancelledError:
        logger.info("Kafka consumer loop cancelled")
    except Exception as e:
        logger.critical("Fatal consumer error: %s", e, exc_info=True)
    finally:
        health_task.cancel()
        await consumer.stop()

async def process_batch(
    messages: List,
    redis_client,
    db_session_maker,
    dlq_producer: KafkaProducerWrapper,
) -> None:
    """Обрабатывает пакет сообщений."""
    pipeline = modelManager.get_pipeline()
    rules = ruleManager.get_rules()

    async with UnitOfWork(db_session_maker) as uow:
        service = ClassificationService(uow, redis_client, pipeline, rules)

        for message in messages:
            req_id: str | None = None
            if message.headers:
                for key, val in message.headers:
                    if key == "X-Request-ID":
                        req_id = val.decode("utf-8")
                        break

            try:
                async with uow.make_savepoint():
                    try:
                        data = json.loads(message.value)
                        event = TransactionNeedCategoryEvent(**data)
                    except Exception as json_err:
                        raise ValueError(f"JSON Error: {json_err}")

                    await service.classify_transaction(event)

            except Exception as e:
                logger.error(
                    "Processing failed for message %s. Sending to DLQ. Reason: %s",
                    message.offset,
                    e,
                )

                headers = [("error", str(e).encode("utf-8"))]
                if req_id:
                    headers.append(("X-Request-ID", req_id.encode("utf-8")))

                try:
                    success = await dlq_producer.send_event(
                        topic=settings.KAFKA.TOPIC_NEED_CATEGORY_DLQ,
                        value=message.value,
                        key=message.key,
                        headers=headers,
                        wait=True,
                    )
                    if not success:
                        raise RuntimeError("DLQ refused message")

                except Exception as dlq_error:
                    logger.critical(
                        "CRITICAL: Failed to send to DLQ. Stopping consumer. Error: %s",
                        dlq_error
                    )
                    raise dlq_error 

        await uow.commit()
