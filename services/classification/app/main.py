import asyncio
import signal
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from arq import create_pool
from arq.connections import RedisSettings
from prometheus_fastapi_instrumentator import Instrumentator
from aiocache import caches
from starlette.responses import JSONResponse
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app import middleware, dependencies, settings, exceptions, logging_config
from app.routers import api
from app.services.ml_service import modelManager
from app.services.rule_manager import ruleManager

@asynccontextmanager
async def lifespan(app: FastAPI):
    logging_config.setup_logging() 
    middleware.logger.info("CategorizationService starting...")
    
    engine = create_async_engine(
        settings.settings.DB.DB_URL,
        pool_size=settings.settings.DB.DB_POOL_SIZE,
        max_overflow=settings.settings.DB.DB_MAX_OVERFLOW,
    )
    db_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    app.state.engine = engine
    app.state.db_session_maker = db_session_maker
    middleware.logger.info("Database engine and session maker created.")

    redis_pool = await dependencies.create_redis_pool()
    app.state.redis_pool = redis_pool
    middleware.logger.info(f"Redis pool created")
    
    arq_settings = RedisSettings.from_dsn(settings.settings.ARQ.REDIS_URL)
    arq_pool = await create_pool(
        arq_settings,
        default_queue_name=settings.settings.ARQ.ARQ_QUEUE_NAME
    )
    app.state.arq_pool = arq_pool
    middleware.logger.info("ARQ Pool initialized")

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
    await modelManager.check_for_updates(db_session_maker)

    middleware.logger.info("Initializing Rule Manager...")
    await ruleManager.check_for_updates(db_session_maker)
    
    async def model_reloader_task():
        """Фоновая задача для обновления модели."""
        while True:
            await asyncio.sleep(60)
            try:
                await modelManager.check_for_updates(db_session_maker)
                await ruleManager.check_for_updates(db_session_maker)
            except Exception as e:
                middleware.logger.error(f"Error in background model reloader: {e}")

    reloader = asyncio.create_task(model_reloader_task())
    
    def signal_handler(sig, frame):
        middleware.logger.info(f"Received signal {sig}. Initiating shutdown...")
        reloader.cancel()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    yield
    
    middleware.logger.info("CategorizationService shutting down...")
    
    reloader.cancel()
    try:
        await asyncio.wait_for(reloader, timeout=5)
    except (asyncio.CancelledError, asyncio.TimeoutError):
        middleware.logger.warning("Model reloader task did not complete in time")
    
    if hasattr(app.state, 'arq_pool') and app.state.arq_pool:
        await app.state.arq_pool.close()
        middleware.logger.info("Arq pool closed.")

    if hasattr(app.state, 'redis_pool') and app.state.redis_pool:
        await dependencies.close_redis_pool(app.state.redis_pool)
        middleware.logger.info("Redis pool closed.")
        
    if hasattr(app.state, 'engine') and app.state.engine:
        await app.state.engine.dispose()
        middleware.logger.info("DB engine disposed.")
    
    middleware.logger.info("CategorizationService shutdown complete")

app = FastAPI(
    title="Classification Service", 
    version="1.0", 
    lifespan=lifespan,
    docs_url="/api/v1/class/docs",
    openapi_url="/api/v1/class/openapi.json"
)

@app.exception_handler(exceptions.ClassificationServiceError)
async def classification_exception_handler(
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

app.middleware("http")(middleware.error_middleware)
Instrumentator().instrument(app).expose(app)
app.include_router(api.router, prefix="/api/v1/class")