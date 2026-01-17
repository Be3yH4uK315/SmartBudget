import asyncio
from arq.connections import RedisSettings
from arq.cron import cron

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.database import get_db_engine, get_session_factory
from app.infrastructure.kafka.producer import KafkaProducerWrapper
from app.workers.tasks import (
    check_goals_deadlines_task,
    run_outbox_loop,
    cleanup_transactions_task,
)

async def on_startup(ctx):
    setup_logging()

    engine = get_db_engine()
    ctx["db_engine"] = engine
    ctx["db_session_maker"] = get_session_factory(engine)

    kafka = KafkaProducerWrapper()
    await kafka.start()
    ctx["kafka_producer"] = kafka

    ctx["outbox_task"] = asyncio.create_task(run_outbox_loop(ctx))

async def on_shutdown(ctx):
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

class WorkerSettings:
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