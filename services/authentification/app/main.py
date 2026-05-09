import logging
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from dadata import Dadata
from fastapi import FastAPI, Request
from fastapi.responses import ORJSONResponse
from redis.asyncio import Redis
from sqlalchemy.exc import SQLAlchemyError
from arq import create_pool
from arq.connections import RedisSettings
from prometheus_fastapi_instrumentator import Instrumentator
from smartbudget_shared.request_logging import setup_request_logging

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.database import get_db_engine, get_session_factory
from app.core import exceptions
from app.api.routes import (
    router as auth_router,
    settings_router as auth_settings_router,
    user_router,
)
from app.api import dependencies

setup_logging()
logger = logging.getLogger(__name__)

try:
    import uvloop

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    logger.info("Using uvloop as event loop policy")
except ImportError:
    logger.warning("uvloop not installed, using default asyncio loop")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Управление ресурсами приложения и их инициализацией."""
    logger.info("=== Application Startup ===")

    engine = get_db_engine()
    app.state.engine = engine
    app.state.db_session_maker = get_session_factory(engine)
    logger.info("Database initialized")

    redis_pool = None
    try:
        redis_pool = await dependencies.create_redis_pool()
        app.state.redis_pool = redis_pool

        redis_client = Redis(connection_pool=redis_pool)
        from fastapi_limiter import FastAPILimiter

        await FastAPILimiter.init(redis_client)

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

    kafka_producer = None
    try:
        from app.infrastructure.kafka.producer import KafkaProducerWrapper

        kafka_producer = KafkaProducerWrapper()
        await kafka_producer.start()
        app.state.kafka_producer = kafka_producer
        logger.info("Kafka producer initialized")
    except Exception as e:
        logger.warning(f"Kafka producer initialization failed: {e}")

    dadata_client = None
    try:
        if settings.GEO.DADATA_API_KEY and settings.GEO.DADATA_SECRET_KEY:
            dadata_client = Dadata(
                settings.GEO.DADATA_API_KEY, settings.GEO.DADATA_SECRET_KEY
            )
            app.state.dadata_client = dadata_client
            logger.info("DaData client initialized")
        else:
            logger.warning("DaData API keys are missing. Geolocation disabled.")
            app.state.dadata_client = None
    except Exception as e:
        logger.error(f"DaData init error: {e}")
        app.state.dadata_client = None

    yield

    logger.info("=== Application Shutdown ===")

    if kafka_producer:
        try:
            await kafka_producer.stop()
            logger.info("Kafka producer closed")
        except Exception as e:
            logger.error(f"Error closing Kafka producer: {e}")

    if arq_pool:
        try:
            await arq_pool.close()
            logger.info("ARQ pool closed")
        except Exception as e:
            logger.error(f"Error closing ARQ pool: {e}")

    if redis_pool:
        try:
            from fastapi_limiter import FastAPILimiter

            await FastAPILimiter.close()
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
    title="Authentication Service",
    version="1.0",
    lifespan=lifespan,
    default_response_class=ORJSONResponse,
    docs_url="/api/v1/auth/docs",
    openapi_url="/api/v1/auth/openapi.json",
)
setup_request_logging(app)

Instrumentator().instrument(app).expose(app)


@app.exception_handler(exceptions.AuthServiceError)
async def auth_service_exception_handler(
    request: Request, exc: exceptions.AuthServiceError
):
    """Обработка бизнес-ошибок сервиса авторизации."""
    status_code = 400
    detail = str(exc)

    if isinstance(
        exc,
        (
            exceptions.InvalidCredentialsError,
            exceptions.InvalidTokenError,
            exceptions.UserInactiveError,
            exceptions.SessionExpiredError,
        ),
    ):
        status_code = 401
    elif isinstance(exc, exceptions.UserNotFoundError):
        status_code = 404
    elif isinstance(exc, exceptions.EmailAlreadyExistsError):
        status_code = 409
    elif isinstance(exc, exceptions.TooManyAttemptsError):
        status_code = 429

    action = "unknown"
    try:
        action = request.url.path.strip("/").split("/")[-1]
    except Exception:
        pass

    logger.warning(f"Service error: {type(exc).__name__}: {detail}")

    return ORJSONResponse(
        status_code=status_code,
        content={"status": "error", "action": action, "detail": detail},
    )


@app.exception_handler(SQLAlchemyError)
async def db_error_handler(request: Request, exc: SQLAlchemyError):
    """Обработка ошибок БД."""
    logger.error(f"Database error: {exc}", exc_info=True)
    return ORJSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Обработка неожиданных ошибок."""
    logger.critical(f"Unhandled exception: {exc}", exc_info=True)
    return ORJSONResponse(status_code=500, content={"detail": "Internal server error"})


app.include_router(auth_router, prefix="/api/v1/auth")
app.include_router(user_router, prefix="/api/v1/user")
app.include_router(auth_settings_router, prefix="/api/v1/settings")
