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
    cleanup_sessions_task,
    enrich_session_task,
    process_outbox_task,
    send_email_task,
)

logger = logging.getLogger(__name__)


async def run_outbox_processor(ctx) -> None:
    """Запуск цикла публикации исходящих сообщений для событий Kafka."""
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
        await asyncio.sleep(1.0)


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
    ctx["outbox_task"] = asyncio.create_task(run_outbox_processor(ctx))
    logger.info("ARQ worker started")


async def on_shutdown(ctx) -> None:
    """Закрытие ресурсов ARQ worker при остановке."""
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
    """Настройки ARQ Worker."""

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
    max_tries = 3
    max_jobs = 20
    keep_result = 60
