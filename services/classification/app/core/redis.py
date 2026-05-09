import logging

from redis.asyncio import ConnectionPool

from app.core.config import settings

logger = logging.getLogger(__name__)


async def create_redis_pool() -> ConnectionPool:
    """Создает пул соединений с Redis."""
    logger.info("Connecting to Redis at %s", settings.ARQ.REDIS_URL)

    return ConnectionPool.from_url(
        settings.ARQ.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
        max_connections=settings.ARQ.REDIS_MAX_CONNECTIONS,
    )


async def close_redis_pool(pool: ConnectionPool) -> None:
    """Закрывает пул соединений с Redis."""
    logger.info("Closing Redis pool")
    await pool.disconnect()
