import logging
from arq.connections import RedisSettings
from arq.cron import cron
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app import settings, logging_config
from app.tasks import retrain, promote, build_dataset

logger = logging.getLogger(__name__)

async def on_startup(ctx):
    """Выполняется при старте воркера Arq."""
    logging_config.setup_logging()
    logger.info(
        f"Arq worker starting. Redis: {settings.settings.ARQ.REDIS_URL}, Queue: {settings.settings.ARQ.ARQ_QUEUE_NAME}"
    )
    engine = create_async_engine(settings.settings.DB.DB_URL)
    db_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    ctx["db_engine"] = engine
    ctx["db_session_maker"] = db_session_maker
    logger.info("Arq: DB engine and session maker injected.")

async def on_shutdown(ctx):
    """Выполняется при остановке воркера Arq."""
    logger.info("Shutting down Arq worker...")
    engine = ctx.get("db_engine")
    if engine:
        await engine.dispose()
        logger.info("Arq: DB engine disposed.")

class WorkerSettings:
    """Настройки для Arq worker."""
    functions = [
        retrain.retrain_model_task,
        promote.validate_and_promote_model,
        build_dataset.build_training_dataset_task
    ]
    on_startup = on_startup
    on_shutdown = on_shutdown
    
    cron_jobs = [
        cron(
            build_dataset.build_training_dataset_task,
            weekday=6,
            hour=0,
            minute=0,
            run_at_startup=False
        ),
        cron(
            retrain.retrain_model_task,
            hour=2, 
            minute=0, 
            run_at_startup=False
        ),
        cron(
            promote.validate_and_promote_model,
            hour=3,
            minute=0,
            run_at_startup=False
        )
    ]
    
    queue_name = settings.settings.ARQ.ARQ_QUEUE_NAME
    redis_settings = RedisSettings.from_dsn(settings.settings.ARQ.REDIS_URL)
    max_tries = 3
    max_jobs = 10