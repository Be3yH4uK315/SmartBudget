import asyncio
import json
import logging
from pathlib import Path
from typing import List

from aiokafka import AIOKafkaConsumer
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.domain.schemas import kafka as schemas
from app.infrastructure.kafka.producer import KafkaProducerWrapper
from app.services.service import GoalService
from app.infrastructure.db.uow import UnitOfWork

logger = logging.getLogger(__name__)
HEALTH_FILE = Path("/tmp/healthy")

BATCH_SIZE = 100

async def keep_alive_task():
    """Фоновая задача, сообщающая Kubernetes, что сервис жив."""
    while True:
        try:
            HEALTH_FILE.touch(exist_ok=True)
        except OSError:
            pass
        await asyncio.sleep(5)

async def consume_loop(db_session_maker, dlq_producer: KafkaProducerWrapper) -> None:
    """Оптимизированный цикл консьюмера с батчингом."""
    consumer = AIOKafkaConsumer(
        settings.KAFKA.KAFKA_TOPIC_TRANSACTION_GOAL,
        bootstrap_servers=settings.KAFKA.KAFKA_BOOTSTRAP_SERVERS,
        group_id=settings.KAFKA.KAFKA_GOALS_GROUP_ID,
        enable_auto_commit=False,
        auto_offset_reset="earliest",
        max_poll_records=BATCH_SIZE, 
    )
    
    await consumer.start()
    logger.info("Kafka Consumer started")
    
    health_task = asyncio.create_task(keep_alive_task())

    try:
        while True:
            result = await consumer.getmany(timeout_ms=1000, max_records=BATCH_SIZE)
            
            for tp, messages in result.items():
                if not messages:
                    continue
                
                await process_batch(messages, db_session_maker, dlq_producer)
                
                await consumer.commit()

    except asyncio.CancelledError:
        logger.info("Consumer loop cancelled")
    except Exception as e:
        logger.critical(f"Fatal consumer error: {e}", exc_info=True)
    finally:
        health_task.cancel()
        await consumer.stop()

async def process_batch(
    messages: List, 
    db_session_maker, 
    dlq_producer: KafkaProducerWrapper
) -> None:
    """Обработка списка сообщений с изоляцией ошибок и DLQ."""
    async with UnitOfWork(db_session_maker) as uow:
        service = GoalService(uow)
        
        for message in messages:
            try:
                async with uow.make_savepoint():
                    try:
                        data = json.loads(message.value)
                        event = schemas.TransactionEvent(**data)
                        await service.update_goal_balance(event)
                    
                    except (json.JSONDecodeError, ValidationError) as e:
                        logger.warning(f"Validation error at offset {message.offset}: {e}")
                        raise ValueError(f"Validation error: {e}")
                    
                    except SQLAlchemyError as e:
                        logger.error(f"Database error at offset {message.offset}: {e}")
                        raise 

            except Exception as e:
                logger.error(f"Processing failed for message {message.offset}. Sending to DLQ. Reason: {e}")

                headers = [("error", str(e).encode("utf-8"))]
                
                success = await dlq_producer.send_event(
                    topic=settings.KAFKA.KAFKA_TOPIC_TRANSACTION_DLQ,
                    value=message.value,
                    key=message.key,
                    headers=headers
                )
                
                if not success:
                    logger.critical(f"CRITICAL: Failed to send message {message.offset} to DLQ!")
                
                continue