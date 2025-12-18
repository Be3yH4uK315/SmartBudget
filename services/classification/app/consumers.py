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
from app.services.ml_service import modelManager

logger = logging.getLogger(__name__)

async def _handlePoisonPill(
    producer: AIOKafkaProducer,
    msg: "aiokafka.structs.ConsumerRecord",
    error: Exception
):
    """
    Обрабатывает ошибочное сообщение, отправляя его в DLQ.
    """
    dlqTopic = settings.settings.KAFKA.TOPIC_NEED_CATEGORY_DLQ
    logger.error(
        f"Failed to process message from {msg.topic} (Offset: {msg.offset}). "
        f"Error: {error}. Sending to DLQ: {dlqTopic}"
    )
    try:
        try:
            message = msg.value.decode('utf-8')
        except UnicodeDecodeError:
            message = msg.value.hex()
            
        dlqEvent = schemas.DLQMessage(
            originalTopic=msg.topic,
            originalMessage=message,
            error=f"{type(error).__name__}: {str(error)}",
            timestamp=datetime.now(timezone.utc)
        )
        await kafka_producer.send_kafka_event(producer, dlqTopic, dlqEvent.model_dump())
    except Exception as e:
        logger.critical(f"FAILED TO SEND TO DLQ: {e}")

async def consumeNeedCategory(
    consumer: AIOKafkaConsumer, 
    producer: AIOKafkaProducer, 
    redis: Redis,
    dbSessionMaker: async_sessionmaker[AsyncSession]
):
    """
    Основной консьюмер: слушает 'transaction.need_category'.
    """
    logger.info("Initializing consumer for 'need_category'...")
    
    await modelManager.checkForUpdates(dbSessionMaker)
    
    healthFile = Path("/tmp/healthy")
        
    try:
        async for msg in consumer:
            try:
                healthFile.touch()
            except OSError:
                pass

            await modelManager.checkForUpdates(dbSessionMaker)
            
            currentPipeline = modelManager.getPipeline()
            logger.debug(f"Received message from {msg.topic} offset={msg.offset}")

            try:
                data = json.loads(msg.value.decode('utf-8'))
                
                async with dbSessionMaker() as session:
                    service = ClassificationService(session, redis, currentPipeline)
                    events = await service.processTransaction(data)

                if events:
                    eventClassified, eventEvents = events
                    await kafka_producer.send_kafka_event(producer, settings.settings.KAFKA.TOPIC_CLASSIFIED, eventClassified)
                    await kafka_producer.send_kafka_event(producer, settings.settings.KAFKA.TOPIC_CLASSIFICATION_EVENTS, eventEvents)
                
                await consumer.commit() 
                
            except (json.JSONDecodeError, KeyError, ValueError, exceptions.InvalidKafkaMessageError) as e:
                await _handlePoisonPill(producer, msg, e)
                await consumer.commit() 
            
            except (SQLAlchemyError, KafkaError) as e:
                logger.error(f"Infrastructure error processing message: {e}. Sleeping 5s.")
                await asyncio.sleep(5)
            
            except Exception as e:
                logger.exception(f"Unexpected error processing message: {e}") 
                await _handlePoisonPill(producer, msg, e)
                await consumer.commit()

    finally:
        logger.info("Consumer 'consume_need_category' stopping...")