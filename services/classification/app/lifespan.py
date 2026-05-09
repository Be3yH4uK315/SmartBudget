import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from arq import create_pool
from arq.connections import RedisSettings
from fastapi import FastAPI

from app.core.config import settings
from app.core.database import get_db_engine, get_session_factory
from app.core.redis import close_redis_pool, create_redis_pool
from app.services.classification.rules import ruleManager
from app.services.ml.manager import modelManager
from init_rules import seed_rules_if_empty

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Инициализирует и корректно закрывает ресурсы API-приложения классификации."""
    logger.info("=== Application Startup ===")

    engine = get_db_engine()
    session_factory = get_session_factory(engine)

    app.state.engine = engine
    app.state.db_session_maker = session_factory
    logger.info("Database initialized")

    redis_pool = None
    arq_pool = None

    try:
        redis_pool = await create_redis_pool()
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

    logger.info("Pre-loading models and rules")
    try:
        await seed_rules_if_empty(session_factory)
        await modelManager.check_for_updates(session_factory)
        await ruleManager.check_for_updates(session_factory)
        logger.info("Models and rules loaded successfully")
    except Exception as exc:
        logger.warning(
            "Failed to pre-load models/rules: %s",
            exc,
            exc_info=True,
        )

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
                await close_redis_pool(redis_pool)
                logger.info("Redis pool closed")
            except Exception as exc:
                logger.error("Error closing Redis pool: %s", exc, exc_info=True)

        try:
            await engine.dispose()
            logger.info("Database connection closed")
        except Exception as exc:
            logger.error("Error disposing engine: %s", exc, exc_info=True)

        logger.info("=== Application Shutdown Complete ===")
