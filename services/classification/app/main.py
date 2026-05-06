import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from arq import create_pool
from arq.connections import RedisSettings
from fastapi.responses import ORJSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.database import get_db_engine, get_session_factory
from app.core.redis import create_redis_pool, close_redis_pool
from app.api.routes import router as api_router

from app.services.ml.manager import modelManager
from app.services.classification.rules import ruleManager
from init_rules import seed_rules_if_empty

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Управление ресурсами приложения классификации."""
    logger.info("=== Application Startup ===")

    engine = get_db_engine()
    session_factory = get_session_factory(engine)
    app.state.engine = engine
    app.state.db_session_maker = session_factory
    logger.info("Database initialized")

    redis_pool = None
    try:
        redis_pool = await create_redis_pool()
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

    logger.info("Pre-loading models and rules...")
    try:
        await seed_rules_if_empty(session_factory)
        await modelManager.check_for_updates(session_factory)
        await ruleManager.check_for_updates(session_factory)
        logger.info("Models and rules loaded successfully")
    except Exception as e:
        logger.warning(f"Failed to pre-load models/rules: {e}")

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
            await close_redis_pool(redis_pool)
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
    title="Classification Service",
    version="1.0",
    lifespan=lifespan,
    default_response_class=ORJSONResponse,
    docs_url="/api/v1/class/docs",
    openapi_url="/api/v1/class/openapi.json",
)

Instrumentator().instrument(app).expose(app)


@app.middleware("http")
async def tracing_middleware(request: Request, call_next):
    """Add request tracing headers."""
    req_id = request.headers.get("X-Request-ID") or request.headers.get(
        "X-Correlation-ID"
    )
    if not req_id:
        import uuid

        req_id = str(uuid.uuid4())

    response = await call_next(request)
    response.headers["X-Request-ID"] = req_id
    return response


app.include_router(api_router, prefix="/api/v1/class")
