import asyncio
import json
import logging
import sys
from pathlib import Path

from aiokafka import AIOKafkaConsumer
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import (
    async_sessionmaker, AsyncSession, create_async_engine, AsyncEngine
)
from sqlalchemy.exc import SQLAlchemyError

from app import (
    settings,
    services,
    exceptions,
    schemas,
    unit_of_work
)

logger = logging.getLogger(__name__)
HEALTH_FILE = Path("/tmp/healthy")


def touch_health_file() -> None:
    try:
        HEALTH_FILE.touch(exist_ok=True)
    except Exception:
        pass

async def consume_transaction_goal(
    consumer: AIOKafkaConsumer,
    db_session_maker: async_sessionmaker[AsyncSession],
) -> None:
    logger.info("Starting transaction consumer loop")

    async for message in consumer:
        try:
            touch_health_file()

            try:
                data = json.loads(message.value)
                event = schemas.TransactionEvent(**data)
            except (json.JSONDecodeError, ValidationError) as e:
                logger.error(
                    "Invalid message, skipping",
                    extra={"offset": message.offset, "error": str(e)},
                )
                await consumer.commit()
                continue

            async with unit_of_work.UnitOfWork(db_session_maker) as uow:
                service = services.GoalService(uow)
                await service.update_goal_balance(event)

            await consumer.commit()

        except (exceptions.InvalidGoalDataError, exceptions.GoalNotFoundError) as e:
            logger.warning(
                "Business error, skipping event",
                extra={"offset": message.offset, "error": str(e)},
            )
            await consumer.commit()

        except SQLAlchemyError as e:
            logger.error(
                "Database error, will retry",
                extra={"offset": message.offset, "error": str(e)},
            )
            await asyncio.sleep(1)

        except Exception as e:
            logger.critical(
                "Fatal consumer error",
                extra={"offset": message.offset},
                exc_info=True,
            )
            break

async def start_consumer() -> None:
    engine: AsyncEngine | None = None
    consumer: AIOKafkaConsumer | None = None

    try:
        engine = create_async_engine(settings.settings.DB.DB_URL)
        session_maker = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        consumer = AIOKafkaConsumer(
            settings.settings.KAFKA.KAFKA_TOPIC_TRANSACTION_GOAL,
            bootstrap_servers=settings.settings.KAFKA.KAFKA_BOOTSTRAP_SERVERS,
            group_id=settings.settings.KAFKA.KAFKA_GOALS_GROUP_ID,
            enable_auto_commit=False,
            auto_offset_reset="earliest",
        )

        await consumer.start()
        await consume_transaction_goal(consumer, session_maker)

    except Exception as e:
        logger.critical("Consumer failed to start", exc_info=True)
        sys.exit(1)

    finally:
        if consumer:
            await consumer.stop()
        if engine:
            await engine.dispose()