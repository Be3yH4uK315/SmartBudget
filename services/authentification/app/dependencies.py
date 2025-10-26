from fastapi import Depends
from redis.asyncio import Redis
from fastapi_limiter import FastAPILimiter
from .settings import settings
from .db import get_db

async def get_redis() -> Redis:
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    yield redis

async def rate_limiter(request, call_next):
    pass