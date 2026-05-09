import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from arq import create_pool
from arq.connections import RedisSettings
from dadata import Dadata
from fastapi import FastAPI
from fastapi_limiter import FastAPILimiter
from redis.asyncio import Redis

from app.api import dependencies
from app.core.config import settings
from app.core.database import get_db_engine, get_session_factory
from app.infrastructure.kafka.producer import KafkaProducerWrapper

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Инициализирует и корректно закрывает внешние ресурсы API-приложения."""
    logger.info("=== Application Startup ===")

    engine = get_db_engine()
    app.state.engine = engine
    app.state.db_session_maker = get_session_factory(engine)
    logger.info("Database initialized")

    redis_pool = None
    arq_pool = None
    kafka_producer = None

    try:
        redis_pool = await dependencies.create_redis_pool()
        app.state.redis_pool = redis_pool

        redis_client = Redis(connection_pool=redis_pool)
        await FastAPILimiter.init(redis_client)

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
        kafka_producer = KafkaProducerWrapper()
        await kafka_producer.start()
        app.state.kafka_producer = kafka_producer
        logger.info("Kafka producer initialized")
    except Exception as exc:
        app.state.kafka_producer = None
        logger.warning("Kafka producer initialization failed: %s", exc, exc_info=True)

    try:
        if settings.GEO.DADATA_API_KEY and settings.GEO.DADATA_SECRET_KEY:
            app.state.dadata_client = Dadata(
                settings.GEO.DADATA_API_KEY,
                settings.GEO.DADATA_SECRET_KEY,
            )
            logger.info("DaData client initialized")
        else:
            app.state.dadata_client = None
            logger.warning("DaData API keys are missing. Geolocation disabled.")
    except Exception as exc:
        app.state.dadata_client = None
        logger.error("DaData init error: %s", exc, exc_info=True)

    try:
        yield
    finally:
        logger.info("=== Application Shutdown ===")

        if kafka_producer:
            try:
                await kafka_producer.stop()
                logger.info("Kafka producer closed")
            except Exception as exc:
                logger.error("Error closing Kafka producer: %s", exc, exc_info=True)

        if arq_pool:
            try:
                await arq_pool.close()
                logger.info("ARQ pool closed")
            except Exception as exc:
                logger.error("Error closing ARQ pool: %s", exc, exc_info=True)

        if redis_pool:
            try:
                await FastAPILimiter.close()
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
