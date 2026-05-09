import logging

from smartbudget_shared.health.checks import (
    ArqHealthCheck,
    DatabaseHealthCheck,
    RedisHealthCheck,
)

logger = logging.getLogger(__name__)


async def get_db_health(engine) -> tuple[str, bool]:
    check = DatabaseHealthCheck(engine)
    return await check.check()


async def get_redis_health(redis_pool) -> tuple[str, bool]:
    check = RedisHealthCheck(redis_pool)
    return await check.check()


async def get_arq_health(arq_pool) -> tuple[str, bool]:
    check = ArqHealthCheck(arq_pool)
    return await check.check()
