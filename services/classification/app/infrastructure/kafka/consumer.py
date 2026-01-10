import logging
import json
import asyncio
from pathlib import Path
from datetime import datetime
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from app.core.config import settings
from app.infrastructure.db.uow import UnitOfWork
from app.domain.schemas.kafka import TransactionNeedCategoryEvent, DLQMessage
from app.services.classification.service import ClassificationService
from app.services.ml.manager import modelManager
from app.services.classification.rules import ruleManager

logger = logging.getLogger(__name__)
HEALTH_FILE = Path("/tmp/healthy")

async def send_to_dlq_safe(producer: AIOKafkaProducer, topic: str, original_msg: bytes, error: str):
    """Отправляет в DLQ."""
    dlq_topic = f"{topic}.dlq"
    try:
        try:
            msg_str = original_msg.decode('utf-8')
        except:
            msg_str = str(original_msg)

        dlq_event = DLQMessage(
            originalTopic=topic,
            originalMessage=msg_str,
            error=str(error),
            timestamp=datetime.now()
        )
        
        payload = dlq_event.model_dump_json().encode('utf-8')
        await producer.send_and_wait(dlq_topic, value=payload)
        logger.warning(f"Sent message to DLQ: {dlq_topic}")
    except Exception as e:
        error_msg = f"CRITICAL: Failed to send to DLQ! Stopping consumer to prevent data loss. Error: {e}"
        logger.critical(error_msg)
        raise RuntimeError(error_msg)


async def consume_loop(redis, db_session_maker):
    logger.info("Initializing consumer for 'need_category'...")
    
    consumer = AIOKafkaConsumer(
        settings.KAFKA.TOPIC_NEED_CATEGORY,
        bootstrap_servers=settings.KAFKA.KAFKA_BOOTSTRAP_SERVERS,
        group_id=settings.KAFKA.KAFKA_GROUP_ID,
        enable_auto_commit=False,
        auto_offset_reset="latest",
        max_poll_records=500,
        request_timeout_ms=30000,
    )
    
    dlq_producer = AIOKafkaProducer(
        bootstrap_servers=settings.KAFKA.KAFKA_BOOTSTRAP_SERVERS
    )

    await consumer.start()
    await dlq_producer.start()
    
    try:
        await modelManager.check_for_updates(db_session_maker)
        await ruleManager.check_for_updates(db_session_maker)
        
        BATCH_SIZE = 100
        
        while True:
            batch_msgs = []
            try:
                result = await consumer.getmany(timeout_ms=1000, max_records=BATCH_SIZE)
                for tp, messages in result.items():
                    batch_msgs.extend(messages)
            except Exception as e:
                logger.error(f"Kafka fetch error: {e}")
                await asyncio.sleep(1)
                continue

            if not batch_msgs:
                try: HEALTH_FILE.touch()
                except: pass
                continue

            try: HEALTH_FILE.touch()
            except: pass
            
            await modelManager.check_for_updates(db_session_maker)
            await ruleManager.check_for_updates(db_session_maker)

            valid_events = []
            msgs_to_commit = []
            
            for msg in batch_msgs:
                try:
                    payload = json.loads(msg.value.decode('utf-8'))
                    event = TransactionNeedCategoryEvent(**payload)
                    valid_events.append(event)
                    msgs_to_commit.append(msg)
                except Exception as e:
                    logger.error(f"Deserialization error: {e}")
                    await send_to_dlq_safe(dlq_producer, msg.topic, msg.value, f"Deserialization: {e}")
                    pass

            if valid_events:
                uow = UnitOfWork(db_session_maker)
                pipeline = modelManager.get_pipeline()
                rules = ruleManager.get_rules()
                service = ClassificationService(uow, redis, pipeline, rules)
                
                try:
                    await service.process_batch(valid_events)
                except Exception as e:
                    logger.error(f"Batch processing error: {e}", exc_info=True)
                    await asyncio.sleep(5)
                    continue 
            try:
                await consumer.commit()
            except Exception as e:
                logger.error(f"Commit failed: {e}")
                
    except asyncio.CancelledError:
        logger.info("Consumer loop cancelled")
    except Exception as e:
        logger.critical(f"Critical consumer loop error: {e}", exc_info=True)
    finally:
        logger.info("Consumer stopping...")
        try:
            await consumer.stop()
            await dlq_producer.stop()
        except:
            pass
