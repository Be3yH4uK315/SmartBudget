from typing import Any

from smartbudget_shared.health.checks import (
    ArqHealthCheck,
    DatabaseHealthCheck,
    RedisHealthCheck,
)


async def get_db_health(engine: Any) -> tuple[str, bool]:
    """Проверяет подключение к базе данных."""
    check = DatabaseHealthCheck(engine)
    return await check.check()


async def get_redis_health(redis_pool: Any) -> tuple[str, bool]:
    """Проверяет подключение к Redis."""
    check = RedisHealthCheck(redis_pool)
    return await check.check()


async def get_arq_health(arq_pool: Any) -> tuple[str, bool]:
    """Проверяет подключение к ARQ."""
    check = ArqHealthCheck(arq_pool)
    return await check.check()
