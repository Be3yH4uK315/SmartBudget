import asyncio
import logging
from redis.asyncio import Redis

from app.core.logging import setup_logging
from app.core.database import get_db_engine, get_session_factory
from app.core.redis import close_redis_pool, create_redis_pool
from app.infrastructure.kafka.consumer import consume_loop

setup_logging()
logger = logging.getLogger(__name__)

async def main():
    logger.info("Starting Kafka Consumer Service...")
    
    engine = get_db_engine()
    session_maker = get_session_factory(engine)
    
    redis_pool = await create_redis_pool()
    redis_client = Redis(connection_pool=redis_pool, decode_responses=True)
    
    try:
        await consume_loop(redis_client, session_maker)
    except asyncio.CancelledError:
        logger.info("Consumer cancelled")
    except Exception as e:
        logger.critical(f"Consumer failed: {e}", exc_info=True)
    finally:
        logger.info("Shutting down consumer resources...")
        await close_redis_pool(redis_pool)
        await engine.dispose()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass