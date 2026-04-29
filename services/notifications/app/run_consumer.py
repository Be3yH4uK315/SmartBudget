import asyncio
import logging
import signal
from arq import create_pool
from arq.connections import RedisSettings

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.database import get_db_engine, get_session_factory
from app.infrastructure.kafka.consumer import consume_loop
from app.infrastructure.kafka.producer import KafkaProducerWrapper

setup_logging()
logger = logging.getLogger(__name__)

async def main() -> None:
    logger.info("Starting Notification Kafka Consumer Service...")

    engine = get_db_engine()
    db_session_maker = get_session_factory(engine)
    dlq_producer = KafkaProducerWrapper()
    
    arq_pool = await create_pool(
        RedisSettings.from_dsn(settings.ARQ.REDIS_URL),
        default_queue_name=settings.ARQ.ARQ_QUEUE_NAME,
    )

    stop_event = asyncio.Event()

    def signal_handler() -> None:
        logger.info("Received shutdown signal. Stopping consumer loop gracefully...")
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, signal_handler)

    consumer_task = None

    try:
        await dlq_producer.start()

        consumer_task = asyncio.create_task(
            consume_loop(
                db_session_maker=db_session_maker,
                arq_pool=arq_pool,
                dlq_producer=dlq_producer,
            )
        )
        await stop_event.wait()

    except asyncio.CancelledError:
        logger.info("Main task cancelled")
    except Exception as exc:
        logger.critical("Main loop failed: %s", exc, exc_info=True)
    finally:
        logger.info("Shutting down consumer resources...")
        if consumer_task:
            consumer_task.cancel()
            try:
                await consumer_task
            except asyncio.CancelledError:
                pass

        await dlq_producer.stop()
        await arq_pool.close()
        await engine.dispose()
        logger.info("Shutdown complete.")

if __name__ == "__main__":
    asyncio.run(main())
