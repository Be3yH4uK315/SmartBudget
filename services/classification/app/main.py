from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from arq import create_pool
from arq.connections import RedisSettings
from aiokafka import AIOKafkaProducer
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from aiocache import caches
from starlette.responses import JSONResponse
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app import middleware, dependencies, settings, exceptions, logging_config
from app.routers import api

@asynccontextmanager
async def lifespan(app: FastAPI):
    logging_config.setup_logging() 
    middleware.logger.info("CategorizationService starting...")
    
    engine = create_async_engine(settings.settings.db.db_url)
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    app.state.db_engine = engine
    app.state.async_session_maker = session_maker
    middleware.logger.info("Database engine and session maker created.")

    redis_pool = await dependencies.create_redis_pool()
    app.state.redis_pool = redis_pool
    middleware.logger.info(f"Redis pool created for {settings.settings.redis.redis_url}")
    
    arq_redis_settings = RedisSettings.from_dsn(settings.settings.redis.redis_url)
    arq_redis_settings.queue_name = settings.settings.arq.arq_queue_name
    arq_pool = await create_pool(arq_redis_settings)
    app.state.arq_pool = arq_pool
    middleware.logger.info(f"Arq pool created for queue '{settings.settings.arq.arq_queue_name}'")

    producer = AIOKafkaProducer(
        bootstrap_servers=settings.settings.kafka.kafka_bootstrap_servers,
        request_timeout_ms=30000,
        retry_backoff_ms=1000
    )
    await producer.start()
    app.state.kafka_producer = producer
    middleware.logger.info(f"AIOKafkaProducer started for {settings.settings.kafka.kafka_bootstrap_servers}")

    caches.set_config({
        'default': {
            'cache': "aiocache.RedisCache",
            'endpoint': settings.settings.redis.redis_url.split('//')[1].split(':')[0],
            'port': int(settings.settings.redis.redis_url.split(':')[-1].split('/')[0]),
            'db': 0,
            'ttl': 3600,
        }
    })
    middleware.logger.info("aiocache initialized with Redis backend.")

    yield
    
    middleware.logger.info("CategorizationService shutting down...")
    
    await app.state.kafka_producer.stop()
    middleware.logger.info("AIOKafkaProducer stopped.")
    
    await arq_pool.close()
    middleware.logger.info("Arq pool closed.")

    await dependencies.close_redis_pool(redis_pool)
    middleware.logger.info("Redis pool closed.")
        
    await app.state.db_engine.dispose()
    middleware.logger.info("DB engine disposed.")

app = FastAPI(
    title="Categorization Service", 
    version="1.0", 
    lifespan=lifespan
)

@app.exception_handler(exceptions.ClassificationServiceError)
async def classification_exception_handler(request: Request, exc: exceptions.ClassificationServiceError):
    status_code = 400
    if isinstance(exc, exceptions.ClassificationResultNotFoundError) or isinstance(exc, exceptions.CategoryNotFoundError):
        status_code = 404
    
    return JSONResponse(
        status_code=status_code,
        content={"detail": str(exc)},
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.settings.frontend_url],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
app.middleware("http")(middleware.error_middleware)
Instrumentator().instrument(app).expose(app)
app.include_router(api.router)