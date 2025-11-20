from fastapi import FastAPI
from contextlib import asynccontextmanager
from redis.asyncio import Redis, ConnectionPool
from arq import create_pool
from arq.connections import RedisSettings
from aiokafka import AIOKafkaProducer
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from aiocache import caches

from app.middleware import setup_logging, error_middleware
from app.dependencies import create_redis_pool, close_redis_pool, engine
from app.settings import settings
from app.middleware import logger
from app.routers.api import router as api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("CategorizationService starting...")
    
    redis_pool = await create_redis_pool()
    app.state.redis_pool = redis_pool
    logger.info(f"Redis pool created for {settings.redis_url}")
    
    arq_redis_settings = RedisSettings.from_dsn(settings.redis_url)
    arq_redis_settings.queue_name = settings.arq_queue_name
    arq_pool = await create_pool(arq_redis_settings)
    app.state.arq_pool = arq_pool
    logger.info(f"Arq pool created for queue '{settings.arq_queue_name}'")

    producer = AIOKafkaProducer(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        request_timeout_ms=30000,
        retry_backoff_ms=1000
    )
    await producer.start()
    app.state.kafka_producer = producer
    logger.info(f"AIOKafkaProducer started for {settings.kafka_bootstrap_servers}")

    caches.set_config({
        'default': {
            'cache': "aiocache.RedisCache",
            'endpoint': settings.redis_url.split('//')[1].split(':')[0],
            'port': int(settings.redis_url.split(':')[-1].split('/')[0]),
            'db': 0,
            'ttl': 3600,
        }
    })
    logger.info("aiocache initialized with Redis backend.")

    yield
    
    logger.info("CategorizationService shutting down...")
    
    if hasattr(app.state, "kafka_producer") and app.state.kafka_producer:
        await app.state.kafka_producer.stop()
        logger.info("AIOKafkaProducer stopped.")
    
    if arq_pool:
        await arq_pool.close()
        logger.info("Arq pool closed.")

    if redis_pool:
        await close_redis_pool(redis_pool)
        logger.info("Redis pool closed.")
        
    await engine.dispose()
    logger.info("DB engine disposed.")

app = FastAPI(
    title="Categorization Service", 
    version="1.0", 
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
app.middleware("http")(error_middleware)
Instrumentator().instrument(app).expose(app)
app.include_router(api_router)