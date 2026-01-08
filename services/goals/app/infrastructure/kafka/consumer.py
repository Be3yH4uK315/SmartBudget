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
from app.services.service import GoalService
from app.infrastructure.db.uow import UnitOfWork

logger = logging.getLogger(__name__)
HEALTH_FILE = Path("/tmp/healthy")

BATCH_SIZE = 100
COMMIT_INTERVAL = 1.0

async def keep_alive_task():
    """Фоновая задача, сообщающая Kubernetes, что сервис жив."""
    while True:
        try:
            HEALTH_FILE.touch(exist_ok=True)
        except OSError:
            pass
        await asyncio.sleep(5)

async def consume_loop(db_session_maker) -> None:
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
                
                await process_batch(messages, db_session_maker)
                
                await consumer.commit()

    except asyncio.CancelledError:
        logger.info("Consumer loop cancelled")
    except Exception as e:
        logger.critical(f"Fatal consumer error: {e}", exc_info=True)
    finally:
        health_task.cancel()
        await consumer.stop()

async def process_batch(messages: List, db_session_maker) -> None:
    """Обработка списка сообщений в одной транзакции (или поштучно)."""
    async with UnitOfWork(db_session_maker) as uow:
        service = GoalService(uow)
        
        for message in messages:
            try:
                data = json.loads(message.value)
                event = schemas.TransactionEvent(**data)
                await service.update_goal_balance(event)
                
            except (json.JSONDecodeError, ValidationError) as e:
                logger.error(f"Skipping invalid message at offset {message.offset}: {e}")
                continue
            
            except SQLAlchemyError as e:
                logger.error(f"Database error processing message {message.offset}: {e}")
                raise e

            except Exception as e:
                logger.error(f"Unexpected error processing message {message.offset}: {e}")
                raise e