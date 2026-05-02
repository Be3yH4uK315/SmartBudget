import asyncio
import logging
import signal

from app.core.database import get_db_engine, get_session_factory
from app.core.logging import setup_logging
from app.infrastructure.kafka.consumer import consume_classified_loop

setup_logging()
logger = logging.getLogger(__name__)


async def main() -> None:
    logger.info("Starting transactions Kafka consumer...")
    engine = get_db_engine()
    db_session_maker = get_session_factory(engine)
    stop_event = asyncio.Event()

    def signal_handler() -> None:
        logger.info("Received shutdown signal")
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, signal_handler)

    consumer_task = asyncio.create_task(consume_classified_loop(db_session_maker))

    try:
        await stop_event.wait()
    finally:
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
