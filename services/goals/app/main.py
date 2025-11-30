import logging
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from arq import create_pool
from arq.connections import RedisSettings
from starlette.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from aiokafka.errors import KafkaError
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.routers import goals
from app import (
    dependencies,
    settings,
    exceptions,
    logging_config
)
from app.kafka_producer import KafkaProducer

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управляет ресурсами (DB, Kafka, Arq) во время жизни приложения."""
    logging_config.setup_logging()
    
    try:
        engine = create_async_engine(settings.settings.db.db_url)
        session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        app.state.db_engine = engine
        app.state.async_session_maker = session_maker
        logger.info("Database engine and session maker created.")
    except Exception as e:
        logger.error(f"Failed to create DB engine: {e}")
        app.state.db_engine = None
        app.state.async_session_maker = None

    try:
        kafka_prod_instance = KafkaProducer() 
        await kafka_prod_instance.start()
        app.state.kafka_producer = kafka_prod_instance
    except KafkaError as e:
        logger.error(f"Failed to start Kafka producer: {e}")
        app.state.kafka_producer = None

    arq_redis_settings = RedisSettings.from_dsn(settings.settings.arq.redis_url)
    arq_pool = await create_pool(
        arq_redis_settings, 
        default_queue_name=settings.settings.arq.arq_queue_name
    )
    app.state.arq_pool = arq_pool
    
    logger.info("Application startup complete.")
    yield
    
    if app.state.kafka_producer:
        await app.state.kafka_producer.stop()
        logger.info("Kafka producer stopped.")
    if arq_pool:
        await arq_pool.close()
    if app.state.db_engine:
        await app.state.db_engine.dispose()
        logger.info("Database engine disposed.")
    
    logger.info("Application shutdown complete.")


app = FastAPI(
    title="Goals Service", 
    version="1.0", 
    lifespan=lifespan
)

@app.exception_handler(exceptions.GoalServiceError)
async def goal_service_exception_handler(request: Request, exc: exceptions.GoalServiceError):
    status_code = 400
    if isinstance(exc, exceptions.GoalNotFoundError):
        status_code = 404
    
    return JSONResponse(
        status_code=status_code,
        content={"detail": str(exc)},
    )

@app.exception_handler(SQLAlchemyError)
async def db_error_middleware(request: Request, exc: SQLAlchemyError):
    logger.error(f"DB error: {exc}")
    return JSONResponse(status_code=500, content={"detail": "Database error"})

app.include_router(goals.router)