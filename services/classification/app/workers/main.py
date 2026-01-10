import asyncio
import logging
from arq.connections import RedisSettings
from arq.cron import cron
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.database import get_db_engine
from app.infrastructure.kafka.producer import KafkaProducerWrapper

from app.workers.ml_tasks import (
    build_dataset_task, 
    retrain_model_task, 
    promote_model_task
)
from app.workers.system_tasks import run_outbox_processor, cleanup_sessions_task

logger = logging.getLogger(__name__)

async def on_startup(ctx):
    setup_logging()
    
    engine = get_db_engine()
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    ctx["db_engine"] = engine
    ctx["db_session_maker"] = session_factory
    kafka = KafkaProducerWrapper()
    for i in range(5):
        try:
            await kafka.start()
            break
        except Exception as e:
            logger.warning(f"Kafka producer init retry {i}: {e}")
            await asyncio.sleep(2)
    ctx["kafka_producer"] = kafka
    ctx['outbox_task'] = asyncio.create_task(run_outbox_processor(ctx))
    logger.info("Worker startup complete.")

async def on_shutdown(ctx):
    logger.info("Worker shutting down...")
    
    if ctx.get('outbox_task'):
        ctx['outbox_task'].cancel()
        try:
            await ctx['outbox_task']
        except asyncio.CancelledError:
            pass
    if ctx.get("kafka_producer"):
        await ctx["kafka_producer"].stop()
    if ctx.get("db_engine"):
        await ctx["db_engine"].dispose()

class WorkerSettings:
    functions = [
        build_dataset_task,
        retrain_model_task,
        promote_model_task,
        cleanup_sessions_task
    ]
    on_startup = on_startup
    on_shutdown = on_shutdown
    
    redis_settings = RedisSettings.from_dsn(settings.ARQ.REDIS_URL)
    queue_name = settings.ARQ.ARQ_QUEUE_NAME
    
    cron_jobs = [
        cron(build_dataset_task, weekday=6, hour=0, minute=0),
        cron(retrain_model_task, weekday=6, hour=2, minute=0),
        cron(promote_model_task, weekday=6, hour=3, minute=0),
        cron(cleanup_sessions_task, minute=30)
    ]
