import asyncio
import logging

from app.core.database import get_db_engine, get_session_factory
from app.core.logging import setup_logging
from app.infrastructure.kafka.consumer import consume_loop
from app.infrastructure.kafka.producer import KafkaProducerWrapper

logger = logging.getLogger(__name__)


async def main() -> None:
    """Запускает Kafka consumer process."""
    setup_logging()
    logger.info("Starting goals Kafka consumer process")

    engine = get_db_engine()
    db_session_maker = get_session_factory(engine)

    dlq_producer = KafkaProducerWrapper()

    try:
        await dlq_producer.start()
        await consume_loop(db_session_maker, dlq_producer)

    finally:
        await dlq_producer.stop()
        await engine.dispose()
        logger.info("Goals Kafka consumer process stopped")


if __name__ == "__main__":
    asyncio.run(main())
