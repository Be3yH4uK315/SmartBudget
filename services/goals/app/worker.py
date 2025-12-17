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
    dbSessionMaker = ctx["db_session_maker"]
    kafka: KafkaProducer = ctx["kafka_producer"]
    
    await touchHealthFile()

    async with dbSessionMaker() as session:
        repository = repositories.GoalRepository(session)
        events = await repository.getPendingOutboxEvents(limit=50)
        
        if not events:
            return

        sentIds = []
        failedUpdates = []

        for event in events:
            try:
                await kafka.sendEvent(event.topic, event.payload, schema=None)
                sentIds.append(event.eventId)
            except Exception as e:
                logger.error(f"Failed to send outbox event {event.eventId}: {e}")
                failedUpdates.append((event.eventId, str(e)))

        if sentIds:
            await repository.deleteOutboxEvents(sentIds)
        for fId, fMsg in failedUpdates:
            await repository.handleFailedOutboxEvent(fId, fMsg)

        await repository.db.commit()
        
        if sentIds:
            logger.info(f"Processed {len(sentIds)} outbox events.")
        if failedUpdates:
            logger.warning(f"Failed to send {len(failedUpdates)} events.")

async def checkGoalsDeadlinesTask(ctx):
    """
    ARQ-задача для проверки сроков целей.
    'ctx' содержит ресурсы из 'onStartup'.
    """
    dbSessionMaker = ctx["db_session_maker"]
    
    await touchHealthFile()

    async with dbSessionMaker() as session:
        try:
            repository = repositories.GoalRepository(session)
            service = services.GoalService(repository)
            await service.check_deadlines()
        except Exception as e:
            logger.error(f"Error in checkGoalsDeadlinesTask: {e}")

async def onStartup(ctx):
    logging_config.setupLogging()
    logger.info("Arq worker starting...")

    engine = create_async_engine(settings.settings.DB.DB_URL)
    dbSessionMaker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    ctx["db_engine"] = engine
    ctx["db_session_maker"] = dbSessionMaker

    kafkaProducer = KafkaProducer()
    await kafkaProducer.start()
    ctx["kafka_producer"] = kafkaProducer

    await touchHealthFile()

async def onShutdown(ctx):
    logger.info("Arq worker shutting down...")
    if ctx.get("db_engine"):
        await ctx["db_engine"].dispose()
    if ctx.get("kafka_producer"):
        await ctx["kafka_producer"].stop()

class WorkerSettings:
    functions = [checkGoalsDeadlinesTask, processOutboxTask]
    on_startup = onStartup
    on_shutdown = onShutdown
    cron_jobs = [
        cron(checkGoalsDeadlinesTask, hour=0, minute=0),
        cron(processOutboxTask, minute=set(range(60))), 
    ]
    queue_name = settings.settings.ARQ.ARQ_QUEUE_NAME
    redis_settings = RedisSettings.from_dsn(settings.settings.ARQ.REDIS_URL)