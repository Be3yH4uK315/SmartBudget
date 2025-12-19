import logging
from pathlib import Path
from arq.connections import RedisSettings
from arq.cron import cron
from sqlalchemy.ext.asyncio import (
    AsyncSession, async_sessionmaker, create_async_engine
)
from sqlalchemy.exc import SQLAlchemyError

from app import (
    settings, 
    logging_config, 
    repositories, 
    services,
    exceptions
)
from app.kafka_producer import KafkaProducer 

logger = logging.getLogger(__name__)
HEALTH_FILE = Path("/tmp/healthy")

async def touch_health_file() -> None:
    """Обновляет файл статуса здоровья для мониторинга."""
    try:
        HEALTH_FILE.touch()
    except OSError as e:
        logger.warning(f"Failed to update health file: {e}")

async def process_outbox_task(ctx) -> None:
    """Обработка событий из Outbox и отправка в Kafka."""
    db_session_maker = ctx["db_session_maker"]
    kafka: KafkaProducer = ctx["kafka_producer"]
    
    await touch_health_file()
    
    try:
        async with db_session_maker() as session:
            repository = repositories.GoalRepository(session)
            events = await repository.get_pending_outbox_events(limit=50)
            
            if not events:
                logger.debug("No pending outbox events")
                return

            sent_count = 0
            failed_count = 0
            errors = []

            for event in events:
                try:
                    success = await kafka.send_event(event.topic, event.payload)
                    if success:
                        await repository.delete_outbox_events([event.event_id])
                        sent_count += 1
                    else:
                        await repository.handle_failed_outbox_event(event.event_id, "Send failed")
                        failed_count += 1
                except Exception as e:
                    logger.error(f"Failed to process outbox event {event.event_id}: {e}")
                    await repository.handle_failed_outbox_event(event.event_id, str(e)[:500])
                    failed_count += 1
                    errors.append(str(e))

            await repository.db.commit()
            
            if sent_count > 0:
                logger.info(f"Processed {sent_count} outbox events")
            if failed_count > 0:
                logger.warning(f"Failed to send {failed_count} events. Errors: {errors[:3]}")
    except SQLAlchemyError as e:
        logger.error(f"Database error in outbox task: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in process_outbox_task: {e}", exc_info=True)

async def check_goals_deadlines_task(ctx) -> None:
    """Проверка сроков целей (выполняется ежедневно в 00:00)."""
    db_session_maker = ctx["db_session_maker"]
    
    await touch_health_file()
    
    try:
        async with db_session_maker() as session:
            repository = repositories.GoalRepository(session)
            service = services.GoalService(repository)
            await service.check_deadlines()
    except exceptions.GoalServiceError as e:
        logger.error(f"Service error in deadline check: {e}")
    except SQLAlchemyError as e:
        logger.error(f"Database error in deadline check: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in check_goals_deadlines_task: {e}", exc_info=True)

async def on_startup(ctx) -> None:
    """Инициализация воркера."""
    logging_config.setup_logging()
    logger.info("ARQ worker starting...")

    try:
        engine = create_async_engine(settings.settings.DB.DB_URL)
        db_session_maker = async_sessionmaker(
            engine, 
            class_=AsyncSession, 
            expire_on_commit=False
        )
        ctx["db_engine"] = engine
        ctx["db_session_maker"] = db_session_maker
        logger.info("Database connection pool created")

        kafka_producer = KafkaProducer()
        await kafka_producer.start()
        ctx["kafka_producer"] = kafka_producer
        logger.info("Kafka producer initialized")

        await touch_health_file()
        logger.info("ARQ worker started successfully")
    except Exception as e:
        logger.critical(f"Failed to start ARQ worker: {e}", exc_info=True)
        raise

async def on_shutdown(ctx) -> None:
    """Graceful shutdown воркера."""
    logger.info("ARQ worker shutting down...")
    
    try:
        if ctx.get("kafka_producer"):
            await ctx["kafka_producer"].stop()
            logger.info("Kafka producer stopped")
    except Exception as e:
        logger.error(f"Error stopping Kafka: {e}")
    
    try:
        if ctx.get("db_engine"):
            await ctx["db_engine"].dispose()
            logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database: {e}")
    
    logger.info("ARQ worker shutdown complete")

class WorkerSettings:
    """Конфигурация ARQ воркера."""
    functions = [check_goals_deadlines_task, process_outbox_task]
    on_startup = on_startup
    on_shutdown = on_shutdown
    cron_jobs = [
        cron(check_goals_deadlines_task, hour=0, minute=0),
        cron(process_outbox_task, minute=set(range(60))),
    ]
    queue_name = settings.settings.ARQ.ARQ_QUEUE_NAME
    redis_settings = RedisSettings.from_dsn(settings.settings.ARQ.REDIS_URL)