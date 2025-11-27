import logging
import json
import asyncio
from uuid import UUID
from datetime import datetime, timezone 
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
import aiokafka
from aiokafka.errors import KafkaError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from redis.asyncio import Redis

from app.dependencies import async_session_maker
from app.models import ClassificationResult, ClassificationSource, Feedback
from app.services.classification_service import ClassificationService
from app.kafka_producer import send_kafka_event
from app.settings import settings

logger = logging.getLogger(__name__)

async def _handle_poison_pill(
    producer: AIOKafkaProducer,
    msg: "aiokafka.structs.ConsumerRecord",
    error: Exception
):
    """
    Обрабатывает ошибочное сообщение, отправляя его в DLQ.
    """
    dlq_topic = settings.topic_need_category_dlq
    logger.error(
        f"Failed to process message from {msg.topic} (Offset: {msg.offset}). "
        f"Error: {error}. Sending to DLQ: {dlq_topic}"
    )
    
    try:
        try:
            message_str = msg.value.decode('utf-8')
        except UnicodeDecodeError:
            message_str = msg.value.hex()
            
        dlq_data = {
            "original_topic": msg.topic,
            "original_message": message_str,
            "error": f"{type(error).__name__}: {str(error)}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        await send_kafka_event(
            producer,
            dlq_topic,
            dlq_data
        )
        logger.info(f"Successfully sent poison pill to {dlq_topic}")
        
    except Exception as dlq_e:
        logger.critical(
            f"!!! FAILED TO SEND TO DLQ !!! Error: {dlq_e}. "
            f"Original Error: {error}. Message might be lost or retried infinitely."
        )

async def consume_need_category(
    consumer: AIOKafkaConsumer, 
    producer: AIOKafkaProducer, 
    redis: Redis,
    ml_pipeline: dict | None
):
    """
    Основной консьюмер: слушает 'transaction.need_category'.
    """
    logger.info("Initializing consumer for 'need_category'...")
    if ml_pipeline:
        logger.info(f"Consumer started with ML model version: {ml_pipeline.get('model_version')}")
    else:
        logger.warning("Consumer started WITHOUT ML model.")
        
    try:
        async for msg in consumer:
            logger.debug(f"Received message from {msg.topic}")
            
            try:
                data = json.loads(msg.value.decode('utf-8'))
                transaction_id = UUID(data['transaction_id'])
                
                lock_key = f"lock:classification:{transaction_id}"
                if await redis.set(lock_key, "locked", nx=True, ex=60):
                    async with async_session_maker() as session:
                        existing = await session.execute(
                            select(ClassificationResult.id).where(ClassificationResult.transaction_id == transaction_id)
                        )
                        if existing.scalar_one_or_none():
                            logger.warning(f"Transaction {transaction_id} already processed. Skipping.")
                            await redis.delete(lock_key)
                            await consumer.commit() 
                            continue

                        service = ClassificationService(session, redis, ml_pipeline)
                        
                        category_id, category_name = await service.apply_rules(
                            merchant=data.get('merchant', ''),
                            mcc=data.get('mcc'),
                            description=data.get('description', '')
                        )
                        
                        source = ClassificationSource.RULES
                        confidence = 1.0
                        model_version = None

                        if not category_id:
                            category_id, category_name, confidence, model_version = await service.apply_ml(
                                data
                            )
                            source = ClassificationSource.ML

                        if not category_id:
                            logger.error(f"Failed to classify transaction {transaction_id} even with fallback.")
                            await redis.delete(lock_key)
                            await consumer.commit() 
                            continue

                        result = ClassificationResult(
                            transaction_id=transaction_id,
                            category_id=category_id,
                            category_name=category_name,
                            confidence=confidence,
                            source=source,
                            model_version=model_version,
                            merchant=data.get('merchant', ''),
                            description=data.get('description', ''),
                            mcc=data.get('mcc')
                        )
                        session.add(result)
                        await session.commit()
                        
                        try:
                            await redis.set(
                                f"classification:{transaction_id}", 
                                json.dumps({"category_name": category_name, "category_id": str(category_id)}),
                                ex=3600
                            )
                        except Exception as e:
                            logger.warning(f"Redis SET failed: {e}")

                        event_data = {
                            "transaction_id": str(transaction_id),
                            "category_id": str(category_id),
                            "category_name": category_name
                        }
                        await send_kafka_event(producer, settings.topic_classified, event_data)
                        await send_kafka_event(producer, settings.topic_classification_events, event_data)
                    
                    await redis.delete(lock_key)
                    await consumer.commit() 
                    logger.debug(f"Committed offset for message {msg.offset}")
                else:
                    logger.debug(f"Lock already acquired for {transaction_id}. Skipping to avoid duplicate processing.")
                    await consumer.commit() 

            except (json.JSONDecodeError, KeyError, ValueError, AttributeError) as e:
                await _handle_poison_pill(producer, msg, e)
                await consumer.commit() 
            
            except (SQLAlchemyError, KafkaError) as e:
                logger.error(f"Infrastructure error processing message: {e}")
                await asyncio.sleep(5)
            
            except Exception as e:
                logger.exception(f"Unexpected error processing message: {e}") 
                await _handle_poison_pill(producer, msg, e)
                await consumer.commit() 

    finally:
        logger.info("Consumer 'consume_need_category' stopping...")
