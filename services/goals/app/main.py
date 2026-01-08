import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from arq import create_pool
from arq.connections import RedisSettings
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.database import get_db_engine, get_session_factory
from app.api.routes import router as goals_router
from app.core import exceptions

setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление ресурсами приложения."""
    logger.info("Application startup initiated")
    
    engine = get_db_engine()
    app.state.engine = engine
    app.state.db_session_maker = get_session_factory(engine)
    
    app.state.arq_pool = await create_pool(
        RedisSettings.from_dsn(settings.ARQ.REDIS_URL),
        default_queue_name=settings.ARQ.ARQ_QUEUE_NAME
    )
    yield
    logger.info("Application shutdown initiated")
        
    await app.state.arq_pool.close()
    await engine.dispose()
        
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

app.include_router(goals_router, prefix="/api/v1/goals")