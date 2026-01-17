import asyncio
import json
import logging
from pathlib import Path
from typing import List
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
BATCH_SIZE = 100

async def keep_alive_task() -> None:
    while True:
        try:
            HEALTH_FILE.touch(exist_ok=True)
        except OSError:
            pass

        await asyncio.sleep(5)

async def consume_loop(
    db_session_maker,
    dlq_producer: KafkaProducerWrapper,
) -> None:
    consumer = AIOKafkaConsumer(
        settings.KAFKA.KAFKA_TOPIC_TRANSACTION_GOAL,
        bootstrap_servers=settings.KAFKA.KAFKA_BOOTSTRAP_SERVERS,
        group_id=settings.KAFKA.KAFKA_GOALS_GROUP_ID,
        enable_auto_commit=False,
        auto_offset_reset="earliest",
        max_poll_records=BATCH_SIZE,
    )

    await consumer.start()
    logger.info("Kafka consumer started")

    health_task = asyncio.create_task(keep_alive_task())

    try:
        while True:
            result = await consumer.getmany(
                timeout_ms=1000,
                max_records=BATCH_SIZE,
            )

            for tp, messages in result.items():
                if not messages:
                    continue

                highwater = consumer.highwater(tp)
                if highwater is not None:
                    current_offset = messages[-1].offset + 1
                    lag = highwater - current_offset
                    metrics.KAFKA_CONSUMER_LAG.labels(
                        topic=tp.topic,
                        partition=tp.partition,
                    ).set(lag)

                await process_batch(
                    messages,
                    db_session_maker,
                    dlq_producer,
                )

            await consumer.commit()

    except asyncio.CancelledError:
        logger.info("Kafka consumer loop cancelled")

    except Exception as e:
        logger.critical(
            "Fatal consumer error: %s",
            e,
            exc_info=True,
        )

    finally:
        health_task.cancel()
        await consumer.stop()

async def process_batch(
    messages: List,
    db_session_maker,
    dlq_producer: KafkaProducerWrapper,
) -> None:
    async with UnitOfWork(db_session_maker) as uow:
        service = GoalService(uow)

        for message in messages:
            req_id: str | None = None
            if message.headers:
                for key, val in message.headers:
                    if key == "X-Request-ID":
                        req_id = val.decode("utf-8")
                        break
            set_request_id(req_id)

            try:
                async with uow.make_savepoint():
                    data = json.loads(message.value)
                    event = schemas.TransactionEvent(**data)
                    await service.update_goal_balance(event)

            except Exception as e:
                logger.error(
                    "Processing failed for message %s. Sending to DLQ. Reason: %s",
                    message.offset,
                    e,
                )
                
                metrics.KAFKA_DLQ_ERRORS.labels(
                    topic=message.topic,
                    reason=type(e).__name__,
                ).inc()

                headers = [("error", str(e).encode("utf-8"))]
                if req_id:
                    headers.append(("X-Request-ID", req_id.encode("utf-8")))

                try:
                    success = await dlq_producer.send_event(
                        topic=settings.KAFKA.KAFKA_TOPIC_TRANSACTION_DLQ,
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
