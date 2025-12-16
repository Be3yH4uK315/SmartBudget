import logging
from pathlib import Path
from arq.connections import RedisSettings
from arq.cron import cron
from sqlalchemy.ext.asyncio import (
    AsyncSession, async_sessionmaker, create_async_engine
)

from app import (
    settings, 
    logging_config, 
    repositories, 
    services
)
from app.kafka_producer import KafkaProducer 

logger = logging.getLogger(__name__)

async def touchHealthFile():
    """Обновляет файл статуса здоровья."""
    try:
        Path("/tmp/healthy").touch()
    except Exception as e:
        logger.error(f"Failed to touch health file: {e}")

async def processOutboxTask(ctx):
    """Задача для вычитывания событий из Outbox и отправки в Kafka."""
    db_maker = ctx["db_session_maker"]
    kafka: KafkaProducer = ctx["kafka_producer"]
    
    await touchHealthFile()

    async with db_maker() as session:
        repo = repositories.GoalRepository(session)
        events = await repo.getPendingOutboxEvents(limit=50)
        
        if not events:
            return

        sent_ids = []
        failed_updates = []

        for event in events:
            try:
                await kafka.sendEvent(event.topic, event.payload, schema=None)
                sent_ids.append(event.eventId)
            except Exception as e:
                logger.error(f"Failed to send outbox event {event.eventId}: {e}")
                failed_updates.append((event.eventId, str(e)))

        if sent_ids:
            await repo.deleteOutboxEvents(sent_ids)
        for f_id, f_msg in failed_updates:
            await repo.handleFailedOutboxEvent(f_id, f_msg)

        await repo.db.commit()
        
        if sent_ids:
            logger.info(f"Processed {len(sent_ids)} outbox events.")
        if failed_updates:
            logger.warning(f"Failed to send {len(failed_updates)} events.")

async def checkGoalsDeadlinesTask(ctx):
    """
    ARQ-задача для проверки сроков целей.
    'ctx' содержит ресурсы из 'onStartup'.
    """
    db_maker = ctx["db_session_maker"]
    
    await touchHealthFile()

    async with db_maker() as session:
        try:
            repo = repositories.GoalRepository(session)
            service = services.GoalService(repo)
            await service.check_deadlines()
        except Exception as e:
            logger.error(f"Error in checkGoalsDeadlinesTask: {e}")

async def onStartup(ctx):
    logging_config.setupLogging()
    logger.info("Arq worker starting...")

    engine = create_async_engine(settings.settings.DB.DB_URL)
    db_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    ctx["db_engine"] = engine
    ctx["db_session_maker"] = db_maker

    kafka_prod = KafkaProducer()
    await kafka_prod.start()
    ctx["kafka_producer"] = kafka_prod

    await touchHealthFile()

async def onShutdown(ctx):
    logger.info("Arq worker shutting down...")
    if ctx.get("db_engine"):
        await ctx["db_engine"].dispose()
    if ctx.get("kafka_producer"):
        await ctx["kafka_producer"].stop()

class WorkerSettings:
    functions = [checkGoalsDeadlinesTask, processOutboxTask]
    onStartup = onStartup
    onShutdown = onShutdown
    cron_jobs = [
        cron(checkGoalsDeadlinesTask, hour=0, minute=0),
        cron(processOutboxTask, minute=set(range(60))), 
    ]
    queue_name = settings.settings.ARQ.ARQ_QUEUE_NAME
    redis_settings = RedisSettings.from_dsn(settings.settings.ARQ.REDIS_URL)