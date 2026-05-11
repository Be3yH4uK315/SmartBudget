import asyncio
import logging
from typing import Any

from arq.connections import RedisSettings
from arq.cron import cron

from app.core.config import settings
from app.core.database import get_db_engine, get_session_factory
from app.core.logging import setup_logging
from app.infrastructure.kafka.producer import KafkaProducerWrapper
from app.workers.tasks import (
    check_goals_deadlines_task,
    cleanup_transactions_task,
    run_outbox_loop,
)

logger = logging.getLogger(__name__)

MAX_JOBS = 100
JOB_TIMEOUT_SECONDS = 120
MAX_TRIES = 3


async def on_startup(ctx: dict[str, Any]) -> None:
    """Инициализирует ресурсы ARQ worker."""
    setup_logging()
    logger.info("Goals ARQ worker starting")

    engine = get_db_engine()
    ctx["db_engine"] = engine
    ctx["db_session_maker"] = get_session_factory(engine)

    kafka_producer = KafkaProducerWrapper()
    await kafka_producer.start()
    ctx["kafka_producer"] = kafka_producer

    ctx["outbox_task"] = asyncio.create_task(run_outbox_loop(ctx))

    logger.info("Goals ARQ worker started")


async def on_shutdown(ctx: dict[str, Any]) -> None:
    """Корректно закрывает ресурсы ARQ worker."""
    logger.info("Goals ARQ worker shutting down")

    outbox_task: asyncio.Task | None = ctx.get("outbox_task")
    if outbox_task:
        outbox_task.cancel()
        try:
            await outbox_task
        except asyncio.CancelledError:
            pass

    kafka_producer: KafkaProducerWrapper | None = ctx.get("kafka_producer")
    if kafka_producer:
        await kafka_producer.stop()

    db_engine = ctx.get("db_engine")
    if db_engine:
        await db_engine.dispose()

    logger.info("Goals ARQ worker stopped")


class WorkerSettings:
    """Настройки ARQ worker."""

    functions = [
        check_goals_deadlines_task,
        cleanup_transactions_task,
    ]

    on_startup = on_startup
    on_shutdown = on_shutdown

    cron_jobs = [
        cron(check_goals_deadlines_task, hour=0, minute=0),
        cron(cleanup_transactions_task, weekday=6, hour=3, minute=0),
    ]

    queue_name = settings.ARQ.ARQ_QUEUE_NAME
    redis_settings = RedisSettings.from_dsn(settings.ARQ.REDIS_URL)

    max_jobs = MAX_JOBS
    job_timeout = JOB_TIMEOUT_SECONDS
    max_tries = MAX_TRIES
