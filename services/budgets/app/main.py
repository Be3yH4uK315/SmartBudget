import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from arq import create_pool
from arq.connections import RedisSettings
from fastapi import FastAPI, Request, Response
from fastapi.responses import ORJSONResponse
from redis.asyncio import ConnectionPool
from sqlalchemy.exc import SQLAlchemyError
from smartbudget_shared.request_logging import setup_request_logging

from app.api.routes import (
    dashboard_router as budget_dashboard_router,
    router as budget_router,
    settings_router as budget_settings_router,
)
from app.core import exceptions
from app.core.config import settings
from app.core.context import set_request_id
from app.core.database import get_db_engine, get_session_factory
from app.core.logging import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Управление ресурсами приложения бюджетов."""
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
    except Exception as exc:
        logger.error("Redis pool initialization failed: %s", exc)

    arq_pool = None
    try:
        arq_pool = await create_pool(
            RedisSettings.from_dsn(settings.ARQ.REDIS_URL),
            default_queue_name=settings.ARQ.ARQ_QUEUE_NAME,
        )
        app.state.arq_pool = arq_pool
        logger.info("ARQ pool initialized")
    except Exception as exc:
        logger.error("ARQ pool initialization failed: %s", exc)

    yield

    logger.info("=== Application Shutdown ===")

    if arq_pool:
        try:
            await arq_pool.close()
            logger.info("ARQ pool closed")
        except Exception as exc:
            logger.error("Error closing ARQ pool: %s", exc)

    if redis_pool:
        try:
            await redis_pool.disconnect()
            logger.info("Redis pool closed")
        except Exception as exc:
            logger.error("Error closing Redis pool: %s", exc)

    if engine:
        try:
            await engine.dispose()
            logger.info("Database connection closed")
        except Exception as exc:
            logger.error("Error disposing engine: %s", exc)

    logger.info("=== Application Shutdown Complete ===")


app = FastAPI(
    title="Budgets Service",
    version="1.0",
    lifespan=lifespan,
    default_response_class=ORJSONResponse,
    docs_url="/api/v1/budget/docs",
    openapi_url="/api/v1/budget/openapi.json",
)
setup_request_logging(app, set_request_id)


@app.exception_handler(exceptions.BudgetServiceError)
async def budget_service_exception_handler(
    request: Request,
    exc: exceptions.BudgetServiceError,
):
    status_code = 400
    if isinstance(exc, exceptions.BudgetNotFoundError):
        status_code = 404
    if isinstance(exc, exceptions.BudgetAlreadyExistsError):
        status_code = 409

    logger.warning("Service error: %s: %s", type(exc).__name__, exc)
    return ORJSONResponse(status_code=status_code, content={"detail": str(exc)})


@app.exception_handler(SQLAlchemyError)
async def db_error_handler(
    request: Request,
    exc: SQLAlchemyError,
):
    logger.error("Database error: %s", exc, exc_info=True)
    return ORJSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


@app.exception_handler(Exception)
async def general_exception_handler(
    request: Request,
    exc: Exception,
):
    logger.critical("Unhandled exception: %s", exc, exc_info=True)
    return ORJSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


app.include_router(budget_router, prefix="/api/v1/budget")
app.include_router(budget_settings_router, prefix="/api/v1/settings")
app.include_router(budget_dashboard_router, prefix="/api/v1/dashboard")
