import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from arq import create_pool
from arq.connections import RedisSettings
from fastapi import FastAPI
from redis.asyncio import ConnectionPool

from app.core.config import settings
from app.core.database import get_db_engine, get_session_factory

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Инициализирует и корректно закрывает ресурсы API-приложения бюджетов."""
    logger.info("=== Application Startup ===")

    engine = get_db_engine()
    app.state.engine = engine
    app.state.db_session_maker = get_session_factory(engine)
    logger.info("Database initialized")

    redis_pool = None
    arq_pool = None

    try:
        redis_pool = ConnectionPool.from_url(
            settings.ARQ.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
        app.state.redis_pool = redis_pool
        logger.info("Redis pool initialized")
    except Exception as exc:
        app.state.redis_pool = None
        logger.error("Redis pool initialization failed: %s", exc, exc_info=True)

    try:
        arq_pool = await create_pool(
            RedisSettings.from_dsn(settings.ARQ.REDIS_URL),
            default_queue_name=settings.ARQ.ARQ_QUEUE_NAME,
        )
        app.state.arq_pool = arq_pool
        logger.info("ARQ pool initialized")
    except Exception as exc:
        app.state.arq_pool = None
        logger.error("ARQ pool initialization failed: %s", exc, exc_info=True)

    try:
        yield
    finally:
        logger.info("=== Application Shutdown ===")

        if arq_pool:
            try:
                await arq_pool.close()
                logger.info("ARQ pool closed")
            except Exception as exc:
                logger.error("Error closing ARQ pool: %s", exc, exc_info=True)

        if redis_pool:
            try:
                await redis_pool.disconnect()
                logger.info("Redis pool closed")
            except Exception as exc:
                logger.error("Error closing Redis pool: %s", exc, exc_info=True)

        try:
            await engine.dispose()
            logger.info("Database connection closed")
        except Exception as exc:
            logger.error("Error disposing engine: %s", exc, exc_info=True)

        logger.info("=== Application Shutdown Complete ===")