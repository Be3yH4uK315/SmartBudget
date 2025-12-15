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

async def touch_health_file():
    """Обновляет файл статуса здоровья."""
    try:
        Path("/tmp/healthy").touch()
    except Exception as e:
        logger.error(f"Failed to touch health file: {e}")

async def process_outbox_task(ctx):
    """Задача для вычитывания событий из Outbox и отправки в Kafka."""
    db_maker = ctx["db_session_maker"]
    kafka: KafkaProducer = ctx["kafka_producer"]
    
    await touch_health_file()

    async with db_maker() as session:
        repo = repositories.GoalRepository(session)
        events = await repo.get_pending_outbox_events(limit=50)
        
        if not events:
            return

        sent_ids = []
        failed_updates = []

        for event in events:
            try:
                await kafka.send_event(event.topic, event.payload, schema=None)
                sent_ids.append(event.id)
            except Exception as e:
                logger.error(f"Failed to send outbox event {event.id}: {e}")
                failed_updates.append((event.id, str(e)))

        if sent_ids:
            await repo.delete_outbox_events(sent_ids)
        for f_id, f_msg in failed_updates:
            await repo.handle_failed_outbox_event(f_id, f_msg)

        await repo.db.commit()
        
        if sent_ids:
            logger.info(f"Processed {len(sent_ids)} outbox events.")
        if failed_updates:
            logger.warning(f"Failed to send {len(failed_updates)} events.")

async def check_goals_deadlines_task(ctx):
    """
    ARQ-задача для проверки сроков целей.
    'ctx' содержит ресурсы из 'on_startup'.
    """
    db_maker = ctx["db_session_maker"]
    
    await touch_health_file()

    async with db_maker() as session:
        try:
            repo = repositories.GoalRepository(session)
            service = services.GoalService(repo)
            await service.check_deadlines()
        except Exception as e:
            logger.error(f"Error in check_goals_deadlines_task: {e}")

async def on_startup(ctx):
    logging_config.setup_logging()
    logger.info("Arq worker starting...")

    engine = create_async_engine(settings.settings.db.db_url)
    db_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    ctx["db_engine"] = engine
    ctx["db_session_maker"] = db_maker

    kafka_prod = KafkaProducer()
    await kafka_prod.start()
    ctx["kafka_producer"] = kafka_prod

    await touch_health_file()

async def on_shutdown(ctx):
    logger.info("Arq worker shutting down...")
    if ctx.get("db_engine"):
        await ctx["db_engine"].dispose()
    if ctx.get("kafka_producer"):
        await ctx["kafka_producer"].stop()

class WorkerSettings:
    functions = [check_goals_deadlines_task, process_outbox_task]
    on_startup = on_startup
    on_shutdown = on_shutdown
    cron_jobs = [
        cron(check_goals_deadlines_task, hour=0, minute=0),
        cron(process_outbox_task, minute=set(range(60))), 
    ]
    queue_name = settings.settings.arq.arq_queue_name
    redis_settings = RedisSettings.from_dsn(settings.settings.arq.redis_url)