from smartbudget_shared.health.checks import (
    DatabaseHealthCheck,
    RedisHealthCheck,
    ArqHealthCheck,
)


async def get_db_health(engine) -> tuple[str, bool]:
    """Проверить подключение к базе данных."""
    check = DatabaseHealthCheck(engine)
    return await check.check()


async def get_redis_health(redis_pool) -> tuple[str, bool]:
    """Проверить подключение к Redis."""
    check = RedisHealthCheck(redis_pool)
    return await check.check()


async def get_arq_health(arq_pool) -> tuple[str, bool]:
    """Проверить подключение к ARQ."""
    check = ArqHealthCheck(arq_pool)
    return await check.check()
