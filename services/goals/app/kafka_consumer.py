import asyncio
import json
import logging
from pathlib import Path
import sys
from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError
from sqlalchemy.ext.asyncio import (
    async_sessionmaker, AsyncSession, create_async_engine, AsyncEngine
)
from pydantic import ValidationError

from app import (
    settings, 
    repositories,
    services, 
    exceptions,
    schemas
)
from app.kafka_producer import KafkaProducer 

logger = logging.getLogger(__name__)

async def consume_transaction_goal(
    consumer: AIOKafkaConsumer, 
    db_maker: async_sessionmaker[AsyncSession]
):
    """
    Главный цикл обработки сообщений из 'transaction.goal'.
    """
    logger.info(f"Starting consumer loop...")
    async for message in consumer:
        try:
            Path("/tmp/healthy").touch()
        except OSError:
            pass

        try:
            try:
                data = json.loads(message.value)
                event = schemas.TransactionEvent(**data)
            except (json.JSONDecodeError, ValidationError) as e: 
                logger.error(f"POISON PILL DETECTED (Offset: {message.offset}): {e}. Skipping.")
                await consumer.commit()
                continue

            async with db_maker() as session:
                repo = repositories.GoalRepository(session)
                service = services.GoalService(repo)
                await service.update_goal_balance(event)

            await consumer.commit()

        except (exceptions.InvalidGoalDataError, exceptions.GoalNotFoundError) as e:
            logger.warning(f"Business logic error (Offset: {message.offset}): {e}. Skipping.")
            await consumer.commit()

        except Exception as e:
            logger.critical(f"CRITICAL FAILURE (Offset: {message.offset}): {e}", exc_info=True)
            raise e

async def start_consumer():
    """Инициализирует и запускает консьюмер и его зависимости."""
    db_engine: AsyncEngine | None = None
    kafka_prod_instance: KafkaProducer | None = None
    consumer: AIOKafkaConsumer | None = None

    try:
        db_engine = create_async_engine(settings.settings.db.db_url)
        db_maker = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
        logger.info("Consumer DB context created.")

        kafka_prod_instance = KafkaProducer()
        await kafka_prod_instance.start()
        logger.info("Consumer Kafka producer started.")

        consumer = AIOKafkaConsumer(
            settings.settings.kafka.kafka_topic_transaction_goal,
            bootstrap_servers=settings.settings.kafka.kafka_bootstrap_servers,
            group_id=settings.settings.kafka.kafka_goals_group_id,
            enable_auto_commit=False,
            auto_offset_reset='earliest'
        )

        started = False
        for i in range(5):
            try:
                await consumer.start()
                started = True
                logger.info("Consumer connected to Kafka.")
                break
            except KafkaError as e:
                logger.warning(f"Kafka not ready, retrying in 5s ({i+1}/5)... {e}")
                await asyncio.sleep(5)
        
        if not started:
            raise RuntimeError("Could not connect to Kafka after retries")

        await consume_transaction_goal(consumer, db_maker, kafka_prod_instance)
        
    except Exception as e:
        logger.critical(f"Consumer process failed: {e}", exc_info=True)
        sys.exit(1) 
        
    finally:
        logger.info("Shutting down consumer process...")
        if consumer:
            await consumer.stop()
            logger.info("Kafka consumer stopped.")
        if kafka_prod_instance:
            await kafka_prod_instance.stop()
            logger.info("Kafka producer stopped.")
        if db_engine:
            await db_engine.dispose()
            logger.info("DB engine disposed.")