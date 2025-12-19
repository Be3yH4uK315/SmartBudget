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
from sqlalchemy.exc import SQLAlchemyError
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
HEALTH_FILE = Path("/tmp/healthy")

async def consume_transaction_goal(
    consumer: AIOKafkaConsumer, 
    db_session_maker: async_sessionmaker[AsyncSession]
) -> None:
    """Основной цикл обработки сообщений."""
    logger.info("Starting transaction consumer loop...")
    processed_count = 0
    error_count = 0

    try:
        async for message in consumer:
            try:
                try:
                    HEALTH_FILE.touch()
                except OSError:
                    pass

                try:
                    data = json.loads(message.value)
                    event = schemas.TransactionEvent(**data)
                except (json.JSONDecodeError, ValidationError) as e: 
                    logger.error(
                        f"Invalid message at offset {message.offset}: {e}. "
                        f"Skipping (poison pill)"
                    )
                    await consumer.commit()
                    error_count += 1
                    continue

                async with db_session_maker() as session:
                    repository = repositories.GoalRepository(session)
                    service = services.GoalService(repository)
                    await service.update_goal_balance(event)

                await consumer.commit()
                processed_count += 1

            except (exceptions.InvalidGoalDataError, exceptions.GoalNotFoundError) as e:
                logger.warning(f"Business logic error at offset {message.offset}: {e}")
                await consumer.commit()
                error_count += 1

            except SQLAlchemyError as e:
                logger.error(f"Database error processing message at offset {message.offset}: {e}")
                error_count += 1

            except Exception as e:
                logger.critical(
                    f"Unexpected error at offset {message.offset}: {e}", 
                    exc_info=True
                )
                error_count += 1
                
    except asyncio.CancelledError:
        logger.info("Consumer cancelled")
    except Exception as e:
        logger.critical(f"Consumer loop failed: {e}", exc_info=True)
        raise
    finally:
        logger.info(
            f"Consumer loop ended: processed={processed_count}, "
            f"errors={error_count}"
        )

async def start_consumer() -> None:
    """Инициализирует и запускает консьюмер."""
    engine: AsyncEngine | None = None
    kafka_producer: KafkaProducer | None = None
    consumer: AIOKafkaConsumer | None = None

    try:
        engine = create_async_engine(settings.settings.DB.DB_URL)
        db_session_maker = async_sessionmaker(
            engine, 
            class_=AsyncSession, 
            expire_on_commit=False
        )
        logger.info("Database connection pool created")

        kafka_producer = KafkaProducer()
        await kafka_producer.start()
        logger.info("Kafka producer started")

        consumer = AIOKafkaConsumer(
            settings.settings.KAFKA.KAFKA_TOPIC_TRANSACTION_GOAL,
            bootstrap_servers=settings.settings.KAFKA.KAFKA_BOOTSTRAP_SERVERS,
            group_id=settings.settings.KAFKA.KAFKA_GOALS_GROUP_ID,
            enable_auto_commit=False,
            auto_offset_reset='earliest',
            session_timeout_ms=30000,
            request_timeout_ms=40000
        )

        max_retries = 5
        connected = False
        for attempt in range(max_retries):
            try:
                await consumer.start()
                connected = True
                logger.info("Consumer connected to Kafka")
                break
            except KafkaError as e:
                if attempt < max_retries - 1:
                    wait_time = 5 * (attempt + 1)
                    logger.warning(
                        f"Kafka unavailable, retry {attempt + 1}/{max_retries} "
                        f"in {wait_time}s: {e}"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    raise RuntimeError(f"Could not connect to Kafka after {max_retries} attempts")
        
        if connected:
            await consume_transaction_goal(consumer, db_session_maker)
        
    except Exception as e:
        logger.critical(f"Consumer failed to start: {e}", exc_info=True)
        sys.exit(1) 
        
    finally:
        logger.info("Shutting down consumer...")
        
        if consumer:
            try:
                await consumer.stop()
                logger.info("Consumer stopped")
            except Exception as e:
                logger.error(f"Error stopping consumer: {e}")
        
        if kafka_producer:
            try:
                await kafka_producer.stop()
                logger.info("Kafka producer stopped")
            except Exception as e:
                logger.error(f"Error stopping Kafka producer: {e}")
        
        if engine:
            try:
                await engine.dispose()
                logger.info("Database connections closed")
            except Exception as e:
                logger.error(f"Error closing database: {e}")
        
        logger.info("Consumer shutdown complete")