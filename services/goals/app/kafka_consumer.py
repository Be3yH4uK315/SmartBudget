import asyncio
import json
import logging
from uuid import UUID
from aiokafka import AIOKafkaConsumer
from sqlalchemy.ext.asyncio import (
    async_sessionmaker, AsyncSession, create_async_engine, AsyncEngine
)

from app import settings, dependencies, repositories, services, exceptions
from app.kafka_producer import KafkaProducer 

logger = logging.getLogger(__name__)

async def consume_transaction_goal(
    consumer: AIOKafkaConsumer, 
    db_maker: async_sessionmaker[AsyncSession],
    kafka: KafkaProducer
):
    """
    Главный цикл обработки сообщений из 'transaction.goal'.
    """
    logger.info(f"Starting consumer for topic '{settings.settings.kafka.kafka_topic_transaction_goal}'...")
    try:
        async for message in consumer:
            logger.debug(f"Received message: {message.value}")
            try:
                data = json.loads(message.value)
                
                async with db_maker() as session:
                    repo = repositories.GoalRepository(session)
                    service = services.GoalService(repo, kafka)
                    await service.update_goal_balance(data)
                    
                await consumer.commit() 
                
            except json.JSONDecodeError:
                logger.error(f"Failed to decode JSON: {message.value}")
            except exceptions.GoalNotFoundError as e:
                logger.warning(f"Consumer warning: {e}")
                await consumer.commit()
            except (exceptions.InvalidGoalDataError, Exception) as e:
                logger.error(f"Error processing message {data}: {e}")
    finally:
        logger.info("Consumer loop stopped.")

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
        while True:
            try:
                logger.info("Attempting to start consumer...")
                await consumer.start()
                logger.info("Consumer started successfully.")
                break  # Выход из цикла, если старт успешен
            except Exception as e:
                logger.warning(f"Failed to start consumer (Kafka not ready?): {e}. Retrying in 5s...")
                await asyncio.sleep(5)
        
        await consume_transaction_goal(consumer, db_maker, kafka_prod_instance)
        
    except Exception as e:
        logger.error(f"Consumer failed to start or run: {e}")
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