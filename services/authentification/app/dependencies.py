from fastapi import Depends
from redis.asyncio import Redis
from app.settings import settings
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

# --- DB ---
engine = create_async_engine(settings.db_url)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session

# --- Redis ---
async def get_redis() -> Redis:
    return Redis.from_url(settings.redis_url, decode_responses=True)