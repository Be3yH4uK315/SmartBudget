import asyncio
import logging
import signal
from aiocache import caches
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app import exceptions, logging_config, settings, consumers, dependencies, repositories
from app.services.ml_service import MLService

logger = logging.getLogger(__name__)

async def load_active_ml_pipeline(session_maker: async_sessionmaker[AsyncSession]) -> dict | None:
    """
    Загружает активную ML-модель из БД и кэша.
    """
    logger.info("Attempting to load ACTIVE ML pipeline...")
    try:
        async with session_maker() as session:
            model_repo = repositories.ModelRepository(session)
            active_model = await model_repo.get_active_model()
            
            if not active_model:
                logger.warning("No ACTIVE model found in database. ML classification will be disabled.")
                return None
            
            logger.info(f"Found active model in DB: version {active_model.version}")
            
            model, vectorizer, class_labels = await MLService.load_prediction_pipeline(
                active_model.version
            )

            if not model:
                raise exceptions.ModelLoadError(f"Failed to load ML model version {active_model.version}")

            logger.info(f"Successfully loaded ML pipeline version: {active_model.version}")
            return {
                "model": model,
                "vectorizer": vectorizer,
                "class_labels": class_labels,
                "model_version": active_model.version
            }
    except Exception as e:
        logger.exception(f"Critical error during ML model loading: {e}")
        return None

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
    logger.info("aiocache initialized with Redis backend.")
    
    ml_pipeline = await load_active_ml_pipeline(session_maker)

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
                logger.error(f"Failed to start Kafka producer (attempt {attempt+1}/{max_retries}): {e}")
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
                logger.error(f"Failed to start Kafka consumers (attempt {attempt+1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    raise
        
        tasks = [
            asyncio.create_task(consumers.consume_need_category(
                consumer_need_cat, producer, redis, ml_pipeline, session_maker
            )),
        ]
        
        loop = asyncio.get_running_loop()
        shutdown_event = asyncio.Event()
        
        def signal_handler():
            logger.info("Received shutdown signal. Initiating graceful shutdown...")
            shutdown_event.set()
        
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, signal_handler)
        
        logger.info("All consumers are running. Awaiting tasks or shutdown signal...")
        
        done, pending = await asyncio.wait(
            tasks + [asyncio.create_task(shutdown_event.wait())],
            return_when=asyncio.FIRST_COMPLETED
        )

        for task in pending:
            task.cancel()

        try:
            await asyncio.gather(*pending, return_exceptions=True)
        except asyncio.CancelledError:
            logger.info("Tasks cancelled during shutdown.")
        except Exception as e:
            logger.error(f"Error during tasks shutdown: {e}")
        
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

        logger.info("Resources closed. Shutdown complete.")

if __name__ == "__main__":
    asyncio.run(main())