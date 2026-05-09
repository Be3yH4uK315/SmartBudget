import asyncio
import logging

from arq.connections import RedisSettings
from arq.cron import cron

from app.core.config import settings
from app.core.database import get_db_engine, get_session_factory
from app.core.logging import setup_logging
from app.infrastructure.kafka.producer import KafkaProducerWrapper
from app.workers.tasks import (
    process_outbox_task,
    renew_monthly_budgets_task,
    run_outbox_loop,
)

logger = logging.getLogger(__name__)


async def on_startup(ctx) -> None:
    """Инициализация ресурсов ARQ worker при запуске."""
    setup_logging()
    logger.info("ARQ worker starting")

    engine = get_db_engine()
    ctx["db_engine"] = engine
    ctx["db_session_maker"] = get_session_factory(engine)

    kafka = KafkaProducerWrapper()
    await kafka.start()
    ctx["kafka_producer"] = kafka
    ctx["outbox_task"] = asyncio.create_task(run_outbox_loop(ctx))
    logger.info("ARQ worker started")


async def on_shutdown(ctx) -> None:
    """Закрытие ресурсов ARQ worker."""
    logger.info("ARQ worker shutting down")

    if ctx.get("outbox_task"):
        ctx["outbox_task"].cancel()
        try:
            await ctx["outbox_task"]
        except asyncio.CancelledError:
            pass

    if ctx.get("kafka_producer"):
        await ctx["kafka_producer"].stop()

    if ctx.get("db_engine"):
        await ctx["db_engine"].dispose()

    logger.info("ARQ worker stopped")


class WorkerSettings:
    """Настройки ARQ worker."""

    functions = [
        process_outbox_task,
        renew_monthly_budgets_task,
    ]
    on_startup = on_startup
    on_shutdown = on_shutdown
    cron_jobs = [
        cron(renew_monthly_budgets_task, day=1, hour=0, minute=5),
    ]
    queue_name = settings.ARQ.ARQ_QUEUE_NAME
    redis_settings = RedisSettings.from_dsn(settings.ARQ.REDIS_URL)
