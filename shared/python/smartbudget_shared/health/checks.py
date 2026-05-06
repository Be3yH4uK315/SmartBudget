import logging
from abc import ABC, abstractmethod

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine
from redis.asyncio import Redis

logger = logging.getLogger(__name__)


class HealthCheck(ABC):
    """Базовый класс для проверки здоровья компонентов приложения."""

    name: str

    @abstractmethod
    async def check(self) -> tuple[str, bool]:
        """Выполняет проверку здоровья компонента."""
        pass


class DatabaseHealthCheck(HealthCheck):
    """Проверка здоровья подключения к базе данных."""

    name = "db"

    def __init__(self, engine: AsyncEngine):
        self.engine = engine

    async def check(self) -> tuple[str, bool]:
        """Проверяет подключение к базе данных, выполняя простой запрос."""
        if not self.engine:
            return "disconnected", False

        try:
            async with self.engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return "ok", True
        except Exception:
            logger.exception("Database health check failed")
            return "failed", False


class RedisHealthCheck(HealthCheck):
    """Проверка здоровья подключения к Redis."""

    name = "redis"

    def __init__(self, redis_pool):
        self.redis_pool = redis_pool

    async def check(self) -> tuple[str, bool]:
        """Проверяет подключение к Redis."""
        if not self.redis_pool:
            return "disconnected", False

        try:
            redis_client = Redis(connection_pool=self.redis_pool)
            try:
                await redis_client.ping()
                return "ok", True
            finally:
                await redis_client.aclose(close_connection_pool=False)
        except Exception:
            logger.exception("Redis health check failed")
            return "failed", False


class ArqHealthCheck(HealthCheck):
    """Проверка здоровья подключения к ARQ."""

    name = "arq"

    def __init__(self, arq_pool):
        self.arq_pool = arq_pool

    async def check(self) -> tuple[str, bool]:
        """Проверяет подключение к ARQ."""
        if not self.arq_pool:
            return "disconnected", False

        try:
            await self.arq_pool.ping()
            return "ok", True
        except Exception:
            logger.exception("ARQ health check failed")
            return "failed", False
