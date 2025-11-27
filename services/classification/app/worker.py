import logging
from arq.connections import RedisSettings
from arq.cron import cron

from app.settings import settings
from app.dependencies import async_session_maker, engine
from app.tasks.retrain import retrain_model_task
from app.tasks.promote import validate_and_promote_model
from app.tasks.build_dataset import build_training_dataset_task

logger = logging.getLogger(__name__)

async def on_startup(ctx):
    """Выполняется при старте воркера Arq."""
    logger.info(
        f"Arq worker starting. Redis: {settings.redis_url}, Queue: {settings.arq_queue_name}"
    )
    ctx["db_session_maker"] = async_session_maker
    logger.info("Arq: DB session maker injected.")

async def on_shutdown(ctx):
    """Выполняется при остановке воркера Arq."""
    logger.info("Shutting down Arq worker...")
    await engine.dispose()
    logger.info("Arq: DB engine disposed.")

class WorkerSettings:
    """Настройки для Arq worker."""
    functions = [
        retrain_model_task,
        validate_and_promote_model,
        build_training_dataset_task
    ]
    on_startup = on_startup
    on_shutdown = on_shutdown
    
    cron_jobs = [
        cron(
            build_training_dataset_task,
            weekday=6,
            hour=0,
            minute=0,
            run_at_startup=False
        ),
        cron(
            retrain_model_task,
            hour=2, 
            minute=0, 
            run_at_startup=False
        ),
        cron(
            validate_and_promote_model,
            hour=3,
            minute=0,
            run_at_startup=False
        )
    ]
    queue_name = settings.arq_queue_name
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    max_tries = 3
    max_jobs = 10