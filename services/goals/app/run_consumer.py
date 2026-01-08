import asyncio
import logging
from app.core.logging import setup_logging
from app.core.database import get_db_engine, get_session_factory
from app.infrastructure.kafka.consumer import consume_loop
from app.infrastructure.kafka.producer import KafkaProducerWrapper

setup_logging()
logger = logging.getLogger(__name__)

async def main():
    logger.info("Starting Kafka Consumer Service...")

    engine = get_db_engine()
    db_session_maker = get_session_factory(engine)
    dlq_producer = KafkaProducerWrapper()
    
    try:
        await dlq_producer.start()
        await consume_loop(db_session_maker, dlq_producer)
        
    except asyncio.CancelledError:
        logger.info("Consumer cancelled")
    except Exception as e:
        logger.critical(f"Consumer failed: {e}", exc_info=True)
    finally:
        logger.info("Shutting down consumer resources...")
        await dlq_producer.stop()
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())