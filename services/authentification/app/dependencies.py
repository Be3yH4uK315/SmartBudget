from contextlib import asynccontextmanager
from redis.asyncio import Redis
from .settings import settings


@asynccontextmanager
async def get_redis():
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    try:
        yield redis
    finally:
        await redis.close()