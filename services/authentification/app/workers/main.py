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
    cleanup_failed_outbox_task,
    cleanup_sessions_task,
    enrich_session_task,
    process_outbox_task,
    send_email_task,
)

logger = logging.getLogger(__name__)

OUTBOX_IDLE_SLEEP_SECONDS = 1.0
MAX_JOBS = 100
JOB_TIMEOUT_SECONDS = 120
MAX_TRIES = 3


async def run_outbox_processor(ctx: dict[str, Any]) -> None:
    """Запускает постоянный цикл публикации outbox-событий в Kafka."""
    logger.info("Outbox worker started")

    while True:
        try:
            processed_count = await process_outbox_task(ctx)
            if processed_count > 0:
                continue

        except asyncio.CancelledError:
            logger.info("Outbox worker stopped")
            break

        except Exception:
            logger.exception("Outbox worker failed")

        await asyncio.sleep(OUTBOX_IDLE_SLEEP_SECONDS)


async def on_startup(ctx: dict[str, Any]) -> None:
    """Инициализирует ресурсы ARQ worker при запуске."""
    setup_logging()
    logger.info("Authentification ARQ worker starting")

    engine = get_db_engine()
    ctx["db_engine"] = engine
    ctx["db_session_maker"] = get_session_factory(engine)

    kafka_producer = KafkaProducerWrapper()
    await kafka_producer.start()
    ctx["kafka_producer"] = kafka_producer

    ctx["outbox_task"] = asyncio.create_task(run_outbox_processor(ctx))

    logger.info("Authentification ARQ worker started")


async def on_shutdown(ctx: dict[str, Any]) -> None:
    """Корректно закрывает ресурсы ARQ worker при остановке."""
    logger.info("Authentification ARQ worker shutting down")

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

    logger.info("Authentification ARQ worker stopped")


class WorkerSettings:
    """Настройки ARQ worker."""

    functions = [
        send_email_task,
        cleanup_sessions_task,
        cleanup_failed_outbox_task,
        enrich_session_task,
    ]

    on_startup = on_startup
    on_shutdown = on_shutdown

    cron_jobs = [
        cron(cleanup_failed_outbox_task, hour=4, minute=0),
        cron(cleanup_sessions_task, hour=3, minute=0),
    ]

    queue_name = settings.ARQ.ARQ_QUEUE_NAME
    redis_settings = RedisSettings.from_dsn(settings.ARQ.REDIS_URL)

    max_jobs = MAX_JOBS
    job_timeout = JOB_TIMEOUT_SECONDS
    max_tries = MAX_TRIES
