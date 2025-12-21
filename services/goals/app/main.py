import logging
from contextlib import asynccontextmanager

from arq import create_pool
from arq.connections import RedisSettings
from fastapi import FastAPI, Request
from starlette.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.routers import goals
from app import (
    settings,
    exceptions,
    logging_config,
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление ресурсами приложения."""
    logging_config.setup_logging()
    logger.info("Application startup initiated")
    
    engine = None
    db_session_maker = None
    arq_pool = None
    
    try:
        try:
            engine = create_async_engine(
                settings.settings.DB.DB_URL,
                pool_size=settings.settings.DB.DB_POOL_SIZE,
                max_overflow=settings.settings.DB.DB_MAX_OVERFLOW,
                echo=False
            )
            db_session_maker = async_sessionmaker(
                engine, 
                class_=AsyncSession, 
                expire_on_commit=False
            )
            app.state.engine = engine
            app.state.db_session_maker = db_session_maker
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

        try:
            arq_settings = RedisSettings.from_dsn(settings.settings.ARQ.REDIS_URL)
            arq_pool = await create_pool(
                arq_settings, 
                default_queue_name=settings.settings.ARQ.ARQ_QUEUE_NAME
            )
            app.state.arq_pool = arq_pool
            logger.info("ARQ Redis pool initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ARQ: {e}")
    
        logger.info("Application startup complete")
        yield
        
    finally:
        logger.info("Application shutdown initiated")
        
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