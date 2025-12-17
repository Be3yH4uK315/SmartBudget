import asyncio
import logging
import signal
from aiocache import caches
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app import logging_config, settings, consumers, dependencies

logger = logging.getLogger(__name__)

async def main():
    logging_config.setupLogging()
    logger.info("Starting Kafka Consumer Service...")
    
    engine = create_async_engine(settings.settings.DB.DB_URL)
    dbSessionMaker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    caches.set_config({
        'default': {
            'cache': "aiocache.RedisCache",
            'endpoint': settings.settings.ARQ.REDIS_URL.split('//')[1].split(':')[0],
            'port': int(settings.settings.ARQ.REDIS_URL.split(':')[-1].split('/')[0]),
            'db': 0,
            'ttl': 3600,
        }
    })
    
    redisPool = None
    producer = None
    consumerNeedCategory = None
    
    maxRetries = 5
    retryDelay = 5
    
    try:
        redisPool = await dependencies.createRedisPool()
        redis = Redis(connection_pool=redisPool)
        
        for attempt in range(maxRetries):
            try:
                producer = AIOKafkaProducer(
                    bootstrap_servers=settings.settings.KAFKA.KAFKA_BOOTSTRAP_SERVERS,
                    request_timeout_ms=30000,
                    acks="all",
                )
                await producer.start()
                break
            except Exception as e:
                logger.error(f"Failed to start Kafka producer (attempt {attempt+1}): {e}")
                if attempt < maxRetries - 1:
                    await asyncio.sleep(retryDelay)
                    retryDelay *= 2
                else:
                    raise
        
        for attempt in range(maxRetries):
            try:
                consumerNeedCategory = AIOKafkaConsumer(
                    settings.settings.KAFKA.TOPIC_NEED_CATEGORY,
                    bootstrap_servers=settings.settings.KAFKA.KAFKA_BOOTSTRAP_SERVERS,
                    group_id=settings.settings.KAFKA.KAFKA_GROUP_ID,
                    auto_offset_reset='latest',
                    enable_auto_commit=False
                )
                await consumerNeedCategory.start()
                break
            except Exception as e:
                logger.error(f"Failed to start Kafka consumers (attempt {attempt+1}): {e}")
                if attempt < maxRetries - 1:
                    await asyncio.sleep(retryDelay)
                    retryDelay *= 2
                else:
                    raise
        
        tasks = [
            asyncio.create_task(consumers.consumeNeedCategory(
                consumerNeedCategory, producer, redis, dbSessionMaker
            )),
        ]
        
        loop = asyncio.get_running_loop()
        shutdownEvent = asyncio.Event()
        
        def signalHandler():
            logger.info("Received shutdown signal...")
            shutdownEvent.set()
        
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, signalHandler)
        
        logger.info("Consumers running. Awaiting shutdown...")
        
        await asyncio.wait(
            tasks + [asyncio.create_task(shutdownEvent.wait())],
            return_when=asyncio.FIRST_COMPLETED
        )

        for task in tasks:
            task.cancel()
        
    except Exception as e:
        logger.exception(f"Consumer service failed critically: {e}")
    finally:
        logger.info("Shutting down consumer service...")
        if producer:
            await producer.stop()
        if consumerNeedCategory:
            await consumerNeedCategory.stop()
        if redisPool:
            await dependencies.closeRedisPool(redisPool)
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())