from fastapi import Depends
from redis.asyncio import Redis
from .settings import settings
from .db import get_db

def get_redis() -> Redis:
    return Redis.from_url(settings.redis_url, decode_responses=True)