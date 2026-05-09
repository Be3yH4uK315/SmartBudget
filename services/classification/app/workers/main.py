import asyncio
import logging
from pathlib import Path
from typing import Any

from arq.connections import RedisSettings
from arq.cron import cron

from app.core.config import settings
from app.core.database import get_db_engine, get_session_factory
from app.core.logging import setup_logging
from app.infrastructure.kafka.producer import KafkaProducerWrapper
from app.workers.ml_tasks import (
    build_dataset_task,
    promote_model_task,
    retrain_model_task,
)
from app.workers.system_tasks import cleanup_sessions_task, run_outbox_processor

logger = logging.getLogger(__name__)

HEALTH_FILE = Path("/tmp/healthy")

KEEP_ALIVE_INTERVAL_SECONDS = 5
KAFKA_START_MAX_ATTEMPTS = 5
KAFKA_START_RETRY_DELAY_SECONDS = 2

MAX_JOBS = 100
JOB_TIMEOUT_SECONDS = 600
MAX_TRIES = 3


async def keep_alive_task() -> None:
    """Периодически обновляет health-файл worker-процесса."""
    while True:
        try:
            HEALTH_FILE.touch(exist_ok=True)
        except OSError:
            logger.debug("Failed to touch worker health file", exc_info=True)

        await asyncio.sleep(KEEP_ALIVE_INTERVAL_SECONDS)


async def on_startup(ctx: dict[str, Any]) -> None:
    """Инициализирует ресурсы ARQ worker."""
    setup_logging()
    logger.info("Classification ARQ worker starting")

    engine = get_db_engine()
    ctx["db_engine"] = engine
    ctx["db_session_maker"] = get_session_factory(engine)

    kafka_producer = await _start_kafka_producer()
    ctx["kafka_producer"] = kafka_producer

    ctx["outbox_task"] = asyncio.create_task(run_outbox_processor(ctx))
    ctx["health_task"] = asyncio.create_task(keep_alive_task())

    logger.info("Classification ARQ worker started")


async def on_shutdown(ctx: dict[str, Any]) -> None:
    """Корректно завершает ARQ worker."""
    logger.info("Classification ARQ worker shutting down")

    await _cancel_task(ctx.get("outbox_task"), "outbox_task")
    await _cancel_task(ctx.get("health_task"), "health_task")

    kafka_producer: KafkaProducerWrapper | None = ctx.get("kafka_producer")
    if kafka_producer:
        await kafka_producer.stop()

    db_engine = ctx.get("db_engine")
    if db_engine:
        await db_engine.dispose()

    logger.info("Classification ARQ worker stopped")


async def _start_kafka_producer() -> KafkaProducerWrapper:
    """Запускает Kafka producer с несколькими попытками."""
    kafka_producer = KafkaProducerWrapper()
    last_error: Exception | None = None

    for attempt in range(1, KAFKA_START_MAX_ATTEMPTS + 1):
        try:
            await kafka_producer.start()
            return kafka_producer

        except Exception as exc:
            last_error = exc
            logger.warning(
                "Kafka producer start retry failed",
                extra={"attempt": attempt},
                exc_info=True,
            )
            await asyncio.sleep(KAFKA_START_RETRY_DELAY_SECONDS)

    raise RuntimeError("Kafka producer failed to start") from last_error


async def _cancel_task(task: asyncio.Task | None, task_name: str) -> None:
    """Отменяет asyncio task и дожидается завершения."""
    if not task:
        return

    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        logger.debug("%s cancelled", task_name)


class WorkerSettings:
    """Настройки ARQ worker."""

    functions = [
        build_dataset_task,
        retrain_model_task,
        promote_model_task,
        cleanup_sessions_task,
    ]

    on_startup = on_startup
    on_shutdown = on_shutdown

    redis_settings = RedisSettings.from_dsn(settings.ARQ.REDIS_URL)
    queue_name = settings.ARQ.ARQ_QUEUE_NAME

    cron_jobs = [
        cron(build_dataset_task, weekday=6, hour=0, minute=0),
        cron(retrain_model_task, weekday=6, hour=2, minute=0),
        cron(promote_model_task, weekday=6, hour=3, minute=0),
        cron(cleanup_sessions_task, minute=30),
    ]

    max_jobs = MAX_JOBS
    job_timeout = JOB_TIMEOUT_SECONDS
    max_tries = MAX_TRIES
