import asyncio
import logging
import signal

from app.core.database import get_db_engine, get_session_factory
from app.core.logging import setup_logging
from app.infrastructure.db.uow import UnitOfWork
from app.infrastructure.kafka.consumer import KafkaConsumerWorker
from app.infrastructure.kafka.producer import KafkaProducerWrapper

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
    db_session_maker = get_session_factory(engine)
    dlq_producer = KafkaProducerWrapper()

    stop_event = asyncio.Event()
    _install_signal_handlers(stop_event)
    worker = KafkaConsumerWorker(db_session_maker, dlq_producer)
    worker_task: asyncio.Task | None = None
    stop_task: asyncio.Task | None = None

    try:
        await dlq_producer.start()
        async with UnitOfWork(db_session_maker) as uow:
            await uow.goals.ensure_current_partition()

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
        await engine.dispose()
        logger.info("Kafka consumer service stopped")

if __name__ == "__main__":
    asyncio.run(main())
