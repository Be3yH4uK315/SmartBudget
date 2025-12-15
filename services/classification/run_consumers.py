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
    logging_config.setup_logging()
    logger.info("Starting Kafka Consumer Service...")
    
    db_engine = create_async_engine(settings.settings.db.db_url)
    session_maker = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    
    caches.set_config({
        'default': {
            'cache': "aiocache.RedisCache",
            'endpoint': settings.settings.redis.redis_url.split('//')[1].split(':')[0],
            'port': int(settings.settings.redis.redis_url.split(':')[-1].split('/')[0]),
            'db': 0,
            'ttl': 3600,
        }
    })
    
    redis_pool = None
    producer = None
    consumer_need_cat = None
    
    max_retries = 5
    retry_delay = 5
    
    try:
        redis_pool = await dependencies.create_redis_pool()
        redis = Redis(connection_pool=redis_pool)
        
        for attempt in range(max_retries):
            try:
                producer = AIOKafkaProducer(
                    bootstrap_servers=settings.settings.kafka.kafka_bootstrap_servers,
                    request_timeout_ms=30000,
                    acks="all",
                )
                await producer.start()
                break
            except Exception as e:
                logger.error(f"Failed to start Kafka producer (attempt {attempt+1}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    raise
        
        for attempt in range(max_retries):
            try:
                consumer_need_cat = AIOKafkaConsumer(
                    settings.settings.kafka.topic_need_category,
                    bootstrap_servers=settings.settings.kafka.kafka_bootstrap_servers,
                    group_id=settings.settings.kafka.kafka_group_id,
                    auto_offset_reset='latest',
                    enable_auto_commit=False
                )
                await consumer_need_cat.start()
                break
            except Exception as e:
                logger.error(f"Failed to start Kafka consumers (attempt {attempt+1}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    raise
        
        tasks = [
            asyncio.create_task(consumers.consume_need_category(
                consumer_need_cat, producer, redis, session_maker
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
        
        await asyncio.wait(
            tasks + [asyncio.create_task(shutdown_event.wait())],
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
        if consumer_need_cat:
            await consumer_need_cat.stop()
        if redis_pool:
            await dependencies.close_redis_pool(redis_pool)
        await db_engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())