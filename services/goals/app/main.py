import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, Response
from fastapi.responses import ORJSONResponse
from prometheus_client import make_asgi_app
from arq import create_pool
from arq.connections import RedisSettings
from redis.asyncio import ConnectionPool
from sqlalchemy.exc import SQLAlchemyError
from smartbudget_shared.request_logging import setup_request_logging

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.database import get_db_engine, get_session_factory
from app.core.context import set_request_id
from app.core import exceptions
from app.api.routes import dashboard_router as goals_dashboard_router
from app.api.routes import router as goals_router

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Управление ресурсами приложения целей."""
    logger.info("=== Application Startup ===")

    engine = get_db_engine()
    app.state.engine = engine
    app.state.db_session_maker = get_session_factory(engine)
    logger.info("Database initialized")

    redis_pool = None
    try:
        redis_pool = ConnectionPool.from_url(
            settings.ARQ.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
        app.state.redis_pool = redis_pool
        logger.info("Redis pool initialized")
    except Exception as e:
        logger.error(f"Redis pool initialization failed: {e}")

    arq_pool = None
    try:
        arq_pool = await create_pool(
            RedisSettings.from_dsn(settings.ARQ.REDIS_URL),
            default_queue_name=settings.ARQ.ARQ_QUEUE_NAME,
        )
        app.state.arq_pool = arq_pool
        logger.info("ARQ pool initialized")
    except Exception as e:
        logger.error(f"ARQ pool initialization failed: {e}")

    yield

    logger.info("=== Application Shutdown ===")

    if arq_pool:
        try:
            await arq_pool.close()
            logger.info("ARQ pool closed")
        except Exception as e:
            logger.error(f"Error closing ARQ pool: {e}")

    if redis_pool:
        try:
            await redis_pool.disconnect()
            logger.info("Redis pool closed")
        except Exception as e:
            logger.error(f"Error closing Redis pool: {e}")

    if engine:
        try:
            await engine.dispose()
            logger.info("Database connection closed")
        except Exception as e:
            logger.error(f"Error disposing engine: {e}")

    logger.info("=== Application Shutdown Complete ===")


app = FastAPI(
    title="Goals Service",
    version="1.0",
    lifespan=lifespan,
    default_response_class=ORJSONResponse,
    docs_url="/api/v1/goals/docs",
    openapi_url="/api/v1/goals/openapi.json",
)
setup_request_logging(app, set_request_id)


metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.exception_handler(exceptions.GoalServiceError)
async def goal_service_exception_handler(
    request: Request,
    exc: exceptions.GoalServiceError,
):
    """Обработка ошибок бизнес-логики."""
    status_code = 400
    if isinstance(exc, exceptions.GoalNotFoundError):
        status_code = 404

    logger.warning(
        "Service error: %s: %s",
        type(exc).__name__,
        exc,
    )

    return ORJSONResponse(
        status_code=status_code,
        content={"detail": str(exc)},
    )


@app.exception_handler(SQLAlchemyError)
async def db_error_handler(
    request: Request,
    exc: SQLAlchemyError,
):
    """Обработка ошибок БД."""
    logger.error(
        "Database error: %s",
        exc,
        exc_info=True,
    )

    return ORJSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


@app.exception_handler(Exception)
async def general_exception_handler(
    request: Request,
    exc: Exception,
):
    """Обработка неожиданных ошибок."""
    logger.critical(
        "Unhandled exception: %s",
        exc,
        exc_info=True,
    )

    return ORJSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


app.include_router(
    goals_router,
    prefix="/api/v1/goals",
)
app.include_router(
    goals_dashboard_router,
    prefix="/api/v1/dashboard",
)
