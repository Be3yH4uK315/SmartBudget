import asyncio
import logging
from arq.connections import RedisSettings
from arq.cron import cron

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.database import get_db_engine, get_session_factory
from app.infrastructure.kafka.producer import KafkaProducerWrapper
from app.workers.tasks import (
    cleanup_failed_outbox_task,
    send_email_task,
    process_outbox_task, 
    cleanup_sessions_task
)

logger = logging.getLogger(__name__)

async def run_outbox_processor(ctx):
    while True:
        try:
            processed_count = await process_outbox_task(ctx)
            if processed_count > 0:
                continue 
        except Exception as e:
            logging.getLogger(__name__).error(f"Outbox loop error: {e}")
        await asyncio.sleep(0.5)

async def on_startup(ctx):
    setup_logging()
    
    engine = get_db_engine()
    ctx["db_engine"] = engine
    ctx["db_session_maker"] = get_session_factory(engine)
    
    kafka = KafkaProducerWrapper()
    await kafka.start()
    ctx["kafka_producer"] = kafka
    ctx['outbox_task'] = asyncio.create_task(run_outbox_processor(ctx))

async def on_shutdown(ctx):
    if ctx.get("kafka_producer"): 
        await ctx["kafka_producer"].stop()
    if ctx.get("db_engine"): 
        await ctx["db_engine"].dispose()
    if ctx.get('outbox_task'):
        ctx['outbox_task'].cancel()

class WorkerSettings:
    """Настройки ARQ Worker."""
    functions = [
        send_email_task,
        cleanup_sessions_task,
        cleanup_failed_outbox_task
    ]
    on_startup = on_startup
    on_shutdown = on_shutdown
    
    cron_jobs = [
        cron(cleanup_failed_outbox_task, hour=4, minute=0),
        cron(cleanup_sessions_task, hour=3, minute=0)
    ]
    
    queue_name = settings.ARQ.ARQ_QUEUE_NAME
    redis_settings = RedisSettings.from_dsn(settings.ARQ.REDIS_URL)
    max_tries = 5
    max_jobs = 20
