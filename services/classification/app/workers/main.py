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
from app.workers.system_tasks import process_outbox_task

async def on_startup(ctx):
    setup_logging()
    
    engine = get_db_engine()
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    ctx["db_engine"] = engine
    ctx["db_session_maker"] = session_factory
    
    kafka = KafkaProducerWrapper()
    await kafka.start()
    ctx["kafka_producer"] = kafka

async def on_shutdown(ctx):
    if ctx.get("kafka_producer"):
        await ctx["kafka_producer"].stop()
    if ctx.get("db_engine"):
        await ctx["db_engine"].dispose()

class WorkerSettings:
    functions = [
        process_outbox_task,
        build_dataset_task,
        retrain_model_task,
        promote_model_task
    ]
    on_startup = on_startup
    on_shutdown = on_shutdown
    
    redis_settings = RedisSettings.from_dsn(settings.ARQ.REDIS_URL)
    queue_name = settings.ARQ.ARQ_QUEUE_NAME
    
    cron_jobs = [
        cron(process_outbox_task, minute={i for i in range(60)}), 
        cron(build_dataset_task, weekday=6, hour=0, minute=0),
        cron(retrain_model_task, hour=2, minute=0),
        cron(promote_model_task, hour=3, minute=0)
    ]