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

from app import middleware, dependencies, repositories, settings, exceptions, logging_config
from app.routers import api
from app.services.ml_service import MLService

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

    middleware.logger.info("Loading ML model for API...")
    try:
        async with app.state.async_session_maker() as session:
            model_repo = repositories.ModelRepository(session)
            active_model = await model_repo.get_active_model()
            
            if active_model:
                model, vectorizer, labels = await MLService.load_prediction_pipeline(active_model.version)
                if model:
                    app.state.ml_pipeline = {
                        "model": model,
                        "vectorizer": vectorizer,
                        "class_labels": labels,
                        "model_version": active_model.version
                    }
                    middleware.logger.info(f"API ML pipeline loaded: v{active_model.version}")
                else:
                    middleware.logger.error("Failed to load model files.")
                    app.state.ml_pipeline = None
            else:
                middleware.logger.warning("No active model found in DB.")
                app.state.ml_pipeline = None
    except Exception as e:
        middleware.logger.error(f"Error loading ML pipeline on startup: {e}")
        app.state.ml_pipeline = None

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
    title="Classification Service", 
    version="1.0", 
    lifespan=lifespan,
    docs_url="/api/v1/class/docs",
    openapi_url="/api/v1/class/openapi.json"
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
    allow_origins=[settings.settings.app.frontend_url],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
app.middleware("http")(middleware.error_middleware)
Instrumentator().instrument(app).expose(app)
app.include_router(api.router, prefix="api/v1/class")