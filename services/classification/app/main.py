import asyncio
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
from app.services.ml_service import modelManager

@asynccontextmanager
async def lifespan(app: FastAPI):
    logging_config.setupLogging() 
    middleware.logger.info("CategorizationService starting...")
    
    engine = create_async_engine(settings.settings.DB.DB_URL)
    dbSessionMaker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    app.state.engine = engine
    app.state.dbSessionMaker = dbSessionMaker
    middleware.logger.info("Database engine and session maker created.")

    redisPool = await dependencies.createRedisPool()
    app.state.redisPool = redisPool
    middleware.logger.info(f"Redis pool created for {settings.settings.ARQ.REDIS_URL}")
    
    arqSettings = RedisSettings.from_dsn(settings.settings.ARQ.REDIS_URL)
    arqPool = await create_pool(
        arqSettings,
        default_queue_name=settings.settings.ARQ.ARQ_QUEUE_NAME
    )
    app.state.arqPool = arqPool
    middleware.logger.info("ARQ Pool initialized")

    kafkaProducer = AIOKafkaProducer(
        bootstrap_servers=settings.settings.KAFKA.KAFKA_BOOTSTRAP_SERVERS,
        request_timeout_ms=30000,
        retry_backoff_ms=1000
    )
    await kafkaProducer.start()
    app.state.kafkaProducer = kafkaProducer
    middleware.logger.info(
        f"AIOKafkaProducer started for {settings.settings.KAFKA.KAFKA_BOOTSTRAP_SERVERS}"
    )

    caches.set_config({
        'default': {
            'cache': "aiocache.RedisCache",
            'endpoint': settings.settings.ARQ.REDIS_URL.split('//')[1].split(':')[0],
            'port': int(settings.settings.ARQ.REDIS_URL.split(':')[-1].split('/')[0]),
            'db': 0,
            'ttl': 3600,
        }
    })

    middleware.logger.info("Initializing Model Manager...")
    await modelManager.checkForUpdates(dbSessionMaker)
    
    async def modelReloaderTask():
        """Фоновая задача для обновления модели в API."""
        while True:
            await asyncio.sleep(60)
            try:
                await modelManager.checkForUpdates(dbSessionMaker)
            except Exception as e:
                middleware.logger.error(f"Error in background model reloader: {e}")

    reloader = asyncio.create_task(modelReloaderTask())

    yield
    
    middleware.logger.info("CategorizationService shutting down...")
    
    reloader.cancel()
    
    await app.state.kafkaProducer.stop()
    middleware.logger.info("AIOKafkaProducer stopped.")
    
    await arqPool.close()
    middleware.logger.info("Arq pool closed.")

    await dependencies.closeRedisPool(redisPool)
    middleware.logger.info("Redis pool closed.")
        
    await app.state.engine.dispose()
    middleware.logger.info("DB engine disposed.")

app = FastAPI(
    title="Classification Service", 
    version="1.0", 
    lifespan=lifespan,
    docs_url="/api/v1/class/docs",
    openapi_url="/api/v1/class/openapi.json"
)

@app.exception_handler(exceptions.ClassificationServiceError)
async def classificationExceptionHandler(
    request: Request, 
    exc: exceptions.ClassificationServiceError
):
    status_code = 400
    if isinstance(exc, exceptions.ClassificationResultNotFoundError) \
        or isinstance(exc, exceptions.CategoryNotFoundError):
        status_code = 404
    
    return JSONResponse(
        status_code=status_code,
        content={"detail": str(exc)},
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.settings.APP.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
app.middleware("http")(middleware.errorMiddleware)
Instrumentator().instrument(app).expose(app)
app.include_router(api.router, prefix="/api/v1/class")