import logging
from redis.asyncio import ConnectionPool
from app.core.config import settings

logger = logging.getLogger(__name__)

async def create_redis_pool() -> ConnectionPool:
    """Создает пул соединений с Redis."""
    logger.info(f"Connecting to Redis at {settings.ARQ.REDIS_URL}...")
    pool = ConnectionPool.from_url(
        settings.ARQ.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
        max_connections=settings.ARQ.REDIS_MAX_CONNECTIONS
    )
    return pool

async def close_redis_pool(pool: ConnectionPool):
    """Закрывает пул соединений."""
    logger.info("Closing Redis pool...")
    await pool.disconnect()