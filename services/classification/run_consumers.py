import asyncio
import logging
import signal
from aiokafka import AIOKafkaConsumer
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, create_async_engine

from app import settings, consumers, logging_config, dependencies

logger = logging.getLogger(__name__)

async def main():
    logging_config.setup_logging()
    logger.info("Starting Kafka Consumer Service...")
    
    engine = create_async_engine(
        settings.settings.DB.DB_URL,
        pool_size=settings.settings.DB.DB_POOL_SIZE,
        max_overflow=settings.settings.DB.DB_MAX_OVERFLOW,
    )
    dbSessionMaker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    redis_pool = None
    consumer_need_category = None
    
    maxRetries = 5
    retryDelay = 5
    
    try:
        redis_pool = await dependencies.create_redis_pool()
        redis = Redis(connection_pool=redis_pool, decode_responses=True)
        
        for attempt in range(maxRetries):
            try:
                consumer_need_category = AIOKafkaConsumer(
                    settings.settings.KAFKA.TOPIC_NEED_CATEGORY,
                    bootstrap_servers=settings.settings.KAFKA.KAFKA_BOOTSTRAP_SERVERS,
                    group_id=settings.settings.KAFKA.KAFKA_GROUP_ID,
                    auto_offset_reset='latest',
                    enable_auto_commit=False
                )
                await consumer_need_category.start()
                break
            except Exception as e:
                logger.error(f"Failed to start Kafka consumers (attempt {attempt+1}): {e}")
                if attempt < maxRetries - 1:
                    await asyncio.sleep(retryDelay)
                    retryDelay *= 2
                else:
                    raise
        
        tasks = [
            asyncio.create_task(consumers.consume_need_category(
                consumer_need_category, redis, dbSessionMaker
            )),
        ]
        
        loop = asyncio.get_running_loop()
        shutdown_event = asyncio.Event()
        
        def signal_handler():
            logger.info("Received shutdown signal...")
            shutdown_event.set()
        
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, signal_handler)
        
        logger.info("Consumers running. Awaiting shutdown...")
        
        _done, pending = await asyncio.wait(
            tasks + [asyncio.create_task(shutdown_event.wait())],
            return_when=asyncio.FIRST_COMPLETED
        )

        for task in pending:
            task.cancel()
        
    except Exception as e:
        logger.exception(f"Consumer service failed critically: {e}")
    finally:
        logger.info("Shutting down consumer service...")
        if consumer_need_category:
            await consumer_need_category.stop()
            logger.info("Kafka consumer stopped")
        if redis_pool:
            await dependencies.close_redis_pool(redis_pool)
            logger.info("Redis pool closed")
        await engine.dispose()
        logger.info("Consumer service shutdown complete")

if __name__ == "__main__":
    asyncio.run(main())