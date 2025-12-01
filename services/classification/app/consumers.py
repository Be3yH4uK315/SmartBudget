import logging
import json
import asyncio
from uuid import UUID
from datetime import datetime, timezone 
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
import aiokafka
from aiokafka.errors import KafkaError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from redis.asyncio import Redis

from app import exceptions, settings, kafka_producer
from app.services.classification_service import ClassificationService

logger = logging.getLogger(__name__)

async def _handle_poison_pill(
    producer: AIOKafkaProducer,
    msg: "aiokafka.structs.ConsumerRecord",
    error: Exception
):
    """
    Обрабатывает ошибочное сообщение, отправляя его в DLQ.
    """
    dlq_topic = settings.settings.kafka.topic_need_category_dlq
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
        
        await kafka_producer.send_kafka_event(
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
    ml_pipeline: dict | None,
    session_maker: async_sessionmaker[AsyncSession]
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
                    async with session_maker() as session:
                        service = ClassificationService(session, redis, ml_pipeline)
                        events = await service.process_transaction(data)
                    
                    if events:
                        event_classified, event_events = events
                        await kafka_producer.send_kafka_event(producer, settings.settings.kafka.topic_classified, event_classified)
                        await kafka_producer.send_kafka_event(producer, settings.settings.kafka.topic_classification_events, event_events)
                    
                    await redis.delete(lock_key)
                    await consumer.commit() 
                    logger.debug(f"Committed offset for message {msg.offset}")
                else:
                    logger.debug(f"Lock already acquired for {transaction_id}. Skipping.")
                    await consumer.commit() 

            except (json.JSONDecodeError, KeyError, ValueError, exceptions.InvalidKafkaMessageError) as e:
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
