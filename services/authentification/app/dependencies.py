from fastapi import Depends, Request
from redis.asyncio import Redis, ConnectionPool
from app.settings import settings
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from typing import AsyncGenerator

# --- DB ---
engine = create_async_engine(settings.db_url)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session

# --- Redis ---
async def get_redis(request: Request) -> Redis:
    pool: ConnectionPool = request.app.state.redis_pool
    return Redis(connection_pool=pool, decode_responses=True)

async def create_redis_pool() -> ConnectionPool:
    return ConnectionPool.from_url(settings.redis_url, decode_responses=True)

async def close_redis_pool(pool: ConnectionPool):
    await pool.disconnect()