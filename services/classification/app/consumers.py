import logging
import json
import asyncio
from pathlib import Path
from datetime import datetime, timezone 
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
import aiokafka
from aiokafka.errors import KafkaError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from redis.asyncio import Redis

from app import exceptions, schemas, settings, kafka_producer
from app.services.classification_service import ClassificationService
from app.services.ml_service import model_manager

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
            
        dlq_event = schemas.DLQMessage(
            original_topic=msg.topic,
            original_message=message_str,
            error=f"{type(error).__name__}: {str(error)}",
            timestamp=datetime.now(timezone.utc)
        )
        await kafka_producer.send_kafka_event(producer, dlq_topic, dlq_event.model_dump())
    except Exception as dlq_e:
        logger.critical(f"FAILED TO SEND TO DLQ: {dlq_e}")

async def consume_need_category(
    consumer: AIOKafkaConsumer, 
    producer: AIOKafkaProducer, 
    redis: Redis,
    session_maker: async_sessionmaker[AsyncSession]
):
    """
    Основной консьюмер: слушает 'transaction.need_category'.
    """
    logger.info("Initializing consumer for 'need_category'...")
    
    await model_manager.check_for_updates(session_maker)
    
    health_file = Path("/tmp/healthy")
        
    try:
        async for msg in consumer:
            try:
                health_file.touch()
            except OSError:
                pass

            await model_manager.check_for_updates(session_maker)
            
            current_pipeline = model_manager.get_pipeline()
            logger.debug(f"Received message from {msg.topic} offset={msg.offset}")

            try:
                data = json.loads(msg.value.decode('utf-8'))
                
                async with session_maker() as session:
                    service = ClassificationService(session, redis, current_pipeline)
                    events = await service.process_transaction(data)

                if events:
                    event_classified, event_events = events
                    await kafka_producer.send_kafka_event(producer, settings.settings.kafka.topic_classified, event_classified)
                    await kafka_producer.send_kafka_event(producer, settings.settings.kafka.topic_classification_events, event_events)
                
                await consumer.commit() 
                
            except (json.JSONDecodeError, KeyError, ValueError, exceptions.InvalidKafkaMessageError) as e:
                await _handle_poison_pill(producer, msg, e)
                await consumer.commit() 
            
            except (SQLAlchemyError, KafkaError) as e:
                logger.error(f"Infrastructure error processing message: {e}. Sleeping 5s.")
                await asyncio.sleep(5)
            
            except Exception as e:
                logger.exception(f"Unexpected error processing message: {e}") 
                await _handle_poison_pill(producer, msg, e)
                await consumer.commit()

    finally:
        logger.info("Consumer 'consume_need_category' stopping...")