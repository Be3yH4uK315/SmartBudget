import asyncio
import logging
import signal

from redis.asyncio import Redis

from app.core.database import get_db_engine, get_session_factory
from app.core.logging import setup_logging
from app.core.redis import close_redis_pool, create_redis_pool
from app.infrastructure.kafka.consumer import KafkaConsumerWorker
from app.infrastructure.kafka.producer import KafkaProducerWrapper
from init_rules import seed_rules_if_empty

setup_logging()
logger = logging.getLogger(__name__)


def _install_signal_handlers(stop_event: asyncio.Event) -> None:
    def signal_handler() -> None:
        logger.info("Received shutdown signal. Stopping Kafka worker...")
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, signal_handler)


async def main() -> None:
    logger.info("Starting Kafka consumer service")

    engine = get_db_engine()
    session_maker = get_session_factory(engine)
    await seed_rules_if_empty(session_maker)

    redis_pool = await create_redis_pool()
    redis_client = Redis(connection_pool=redis_pool, decode_responses=True)

    dlq_producer = KafkaProducerWrapper()
    stop_event = asyncio.Event()
    _install_signal_handlers(stop_event)

    worker = KafkaConsumerWorker(
        redis_client=redis_client,
        db_session_maker=session_maker,
        dlq_producer=dlq_producer,
    )
    worker_task: asyncio.Task | None = None
    stop_task: asyncio.Task | None = None

    try:
        await dlq_producer.start()
        worker_task = asyncio.create_task(worker.run())
        stop_task = asyncio.create_task(stop_event.wait())
        done, _ = await asyncio.wait(
            {worker_task, stop_task},
            return_when=asyncio.FIRST_COMPLETED,
        )

        if worker_task in done:
            await worker_task

    except asyncio.CancelledError:
        logger.info("Kafka consumer service cancelled")
        raise
    except Exception:
        logger.exception("Kafka consumer service failed")
        raise
    finally:
        logger.info("Shutting down Kafka consumer resources")

        if worker_task and not worker_task.done():
            worker_task.cancel()
            try:
                await worker_task
            except asyncio.CancelledError:
                pass

        if stop_task and not stop_task.done():
            stop_task.cancel()

        await dlq_producer.stop()
        await close_redis_pool(redis_pool)
        await engine.dispose()
        logger.info("Kafka consumer service stopped")


if __name__ == "__main__":
    asyncio.run(main())
