import json
import logging
from uuid import UUID
from aiokafka import AIOKafkaConsumer
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from app import settings, dependencies, repositories, services, exceptions
from app.kafka_producer import KafkaProducer, kafka_producer

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
    db_maker = dependencies.get_async_session_maker()
    await kafka_producer.start()

    consumer = AIOKafkaConsumer(
        settings.settings.kafka.kafka_topic_transaction_goal,
        bootstrap_servers=settings.settings.kafka.kafka_bootstrap_servers,
        group_id=settings.settings.kafka.kafka_goals_group_id,
        enable_auto_commit=False,
        auto_offset_reset='earliest'
    )
    
    try:
        await consumer.start()
        await consume_transaction_goal(consumer, db_maker, kafka_producer)
    except Exception as e:
        logger.error(f"Consumer failed to start or run: {e}")
    finally:
        await consumer.stop()
        await kafka_producer.stop()