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
    settings,
    exceptions,
    logging_config,
)
from app.kafka_producer import KafkaProducer

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление ресурсами приложения."""
    logging_config.setup_logging()
    logger.info("Application startup initiated")
    
    engine = None
    db_session_maker = None
    kafka_producer = None
    arq_pool = None
    
    try:
        try:
            engine = create_async_engine(
                settings.settings.DB.DB_URL,
                pool_size=20,
                max_overflow=0,
                echo=False
            )
            db_session_maker = async_sessionmaker(
                engine, 
                class_=AsyncSession, 
                expire_on_commit=False
            )
            app.state.engine = engine
            app.state.dbSessionMaker = db_session_maker
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            app.state.engine = None
            app.state.dbSessionMaker = None
            raise

        try:
            kafka_producer = KafkaProducer() 
            await kafka_producer.start()
            app.state.kafkaProducer = kafka_producer
            logger.info("Kafka producer initialized successfully")
        except KafkaError as e:
            logger.error(f"Failed to initialize Kafka: {e}")
            app.state.kafkaProducer = None

        try:
            arq_settings = RedisSettings.from_dsn(settings.settings.ARQ.REDIS_URL)
            arq_pool = await create_pool(
                arq_settings, 
                default_queue_name=settings.settings.ARQ.ARQ_QUEUE_NAME
            )
            app.state.arqPool = arq_pool
            logger.info("ARQ Redis pool initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ARQ: {e}")
            app.state.arqPool = None
    
        logger.info("Application startup complete")
        yield
        
    finally:
        logger.info("Application shutdown initiated")
        
        if kafka_producer:
            try:
                await kafka_producer.stop()
                logger.info("Kafka producer stopped")
            except Exception as e:
                logger.error(f"Error stopping Kafka: {e}")
        
        if arq_pool:
            try:
                await arq_pool.close()
                logger.info("ARQ pool closed")
            except Exception as e:
                logger.error(f"Error closing ARQ pool: {e}")
        
        if engine:
            try:
                await engine.dispose()
                logger.info("Database disposed")
            except Exception as e:
                logger.error(f"Error disposing database: {e}")
        
        logger.info("Application shutdown complete")


app = FastAPI(
    title="Goals Service", 
    version="1.0", 
    lifespan=lifespan,
    docs_url="/api/v1/goals/docs",
    openapi_url="/api/v1/goals/openapi.json"
)

@app.exception_handler(exceptions.GoalServiceError)
async def goal_service_exception_handler(request: Request, exc: exceptions.GoalServiceError):
    """Обработка ошибок сервиса."""
    status_code = 400
    if isinstance(exc, exceptions.GoalNotFoundError):
        status_code = 404
    
    logger.warning(f"Service error: {type(exc).__name__}: {exc}")
    return JSONResponse(
        status_code=status_code,
        content={"detail": str(exc)},
    )

@app.exception_handler(SQLAlchemyError)
async def db_error_handler(request: Request, exc: SQLAlchemyError):
    """Обработка ошибок БД."""
    logger.error(f"Database error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500, 
        content={"detail": "Internal server error"}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Обработка неожиданных ошибок."""
    logger.critical(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

app.include_router(goals.router, prefix="/api/v1/goals")