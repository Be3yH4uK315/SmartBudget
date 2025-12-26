import logging
import json
import asyncio
from pathlib import Path
from aiokafka import AIOKafkaConsumer
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from redis.asyncio import Redis

from app import schemas, unit_of_work
from app.services.classification_service import ClassificationService
from app.services.ml_service import modelManager
from app.services.rule_manager import ruleManager

logger = logging.getLogger(__name__)
HEALTH_FILE = Path("/tmp/healthy")

async def consume_need_category(
    consumer: AIOKafkaConsumer, 
    redis: Redis,
    db_session_maker: async_sessionmaker[AsyncSession]
):
    """
    Основной консьюмер: слушает 'transaction.need_category'.
    Использует Outbox паттерн: не отправляет сообщения в Kafka напрямую.
    """
    logger.info("Initializing consumer for 'need_category'...")
    
    await modelManager.check_for_updates(db_session_maker)
    await ruleManager.check_for_updates(db_session_maker)
    
    try:
        async for msg in consumer:
            try:
                try: HEALTH_FILE.touch()
                except OSError: pass

                await modelManager.check_for_updates(db_session_maker)
                await ruleManager.check_for_updates(db_session_maker)
                
                try:
                    data = json.loads(msg.value.decode('utf-8'))
                    event = schemas.TransactionNeedCategoryEvent(**data)
                except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as e:
                    logger.error(f"Invalid message offset {msg.offset}: {e}. Skipping.")
                    await consumer.commit()
                    continue

                pipeline = modelManager.get_pipeline()
                rules = ruleManager.get_rules()

                uow = unit_of_work.UnitOfWork(db_session_maker)

                service = ClassificationService(uow, redis, pipeline, rules)
                await service.process_transaction(event.model_dump())
                
                await consumer.commit()

            except SQLAlchemyError as e:
                logger.error(f"Infrastructure error (DB): {e}. Will retry.")
                await asyncio.sleep(1)
            
            except Exception as e:
                logger.critical(f"Unexpected error at offset {msg.offset}: {e}", exc_info=True)
                await asyncio.sleep(5)

    finally:
        logger.info("Consumer 'consume_need_category' stopping...")