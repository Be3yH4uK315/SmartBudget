import logging
import json
import asyncio
from pathlib import Path
from aiokafka import AIOKafkaConsumer

from app.core.config import settings
from app.infrastructure.db.uow import UnitOfWork
from app.domain.schemas.kafka import TransactionNeedCategoryEvent
from app.services.classification.service import ClassificationService
from app.services.ml.manager import modelManager
from app.services.classification.rules import ruleManager

logger = logging.getLogger(__name__)
HEALTH_FILE = Path("/tmp/healthy")

async def consume_loop(redis, db_session_maker):
    """
    Основной консьюмер: слушает 'transaction.need_category'.
    Использует Outbox паттерн: не отправляет сообщения в Kafka напрямую.
    """
    logger.info("Initializing consumer for 'need_category'...")
    consumer = AIOKafkaConsumer(
        settings.KAFKA.TOPIC_NEED_CATEGORY,
        bootstrap_servers=settings.KAFKA.KAFKA_BOOTSTRAP_SERVERS,
        group_id=settings.KAFKA.KAFKA_GROUP_ID,
        enable_auto_commit=False,
        auto_offset_reset="latest",
        request_timeout_ms=30000,
    )
    await consumer.start()
    
    try:
        await modelManager.check_for_updates(db_session_maker)
        await ruleManager.check_for_updates(db_session_maker)
    except Exception as e:
        logger.error(f"Initial resource loading failed: {e}")
    
    try:
        async for msg in consumer:
            try:
                try: 
                    HEALTH_FILE.touch()
                except OSError: 
                    pass

                await modelManager.check_for_updates(db_session_maker)
                await ruleManager.check_for_updates(db_session_maker)
                
                uow = UnitOfWork(db_session_maker)
                
                payload = json.loads(msg.value.decode('utf-8'))
                event = TransactionNeedCategoryEvent(**payload)

                pipeline = modelManager.get_pipeline()
                rules = ruleManager.get_rules()

                service = ClassificationService(uow, redis, pipeline, rules)
                await service.process_transaction(event)
                
                await consumer.commit()
            
            except Exception as e:
                logger.critical(f"Unexpected error at offset {msg.offset}: {e}", exc_info=True)
                await asyncio.sleep(5)

    finally:
        logger.info("Consumer 'consume_need_category' stopping...")
        await consumer.stop()