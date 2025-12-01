from fastapi import Request, HTTPException, Depends
from sqlalchemy.ext.asyncio import (
    AsyncSession, create_async_engine, async_sessionmaker
)
from redis.asyncio import Redis, ConnectionPool
from arq.connections import ArqRedis
from aiokafka import AIOKafkaProducer
from typing import AsyncGenerator

from app import settings

engine = create_async_engine(settings.settings.db_url)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Обеспечивает асинхронный сеанс работы с базой данных."""
    async with async_session_maker() as session:
        yield session

async def get_redis(request: Request) -> AsyncGenerator[Redis, None]:
    """Обеспечивает подключение Redis из пула."""
    pool: ConnectionPool = request.app.state.redis_pool
    redis = Redis(connection_pool=pool, decode_responses=True)
    try:
        yield redis
    finally:
        await redis.aclose()

async def create_redis_pool() -> ConnectionPool:
    """Создает пул подключений Redis."""
    return ConnectionPool.from_url(settings.settings.redis_url, decode_responses=True)

async def close_redis_pool(pool: ConnectionPool):
    """Закрывает пул подключений Redis."""
    await pool.disconnect()

async def get_arq_pool(request: Request) -> AsyncGenerator[ArqRedis, None]:
    """Предоставляет пул Arq."""
    arq_pool: ArqRedis = request.app.state.arq_pool
    try:
        yield arq_pool
    finally:
        pass

async def get_kafka_producer(request: Request) -> AIOKafkaProducer:
    """Зависимость для получения Kafka-продюсера."""
    try:
        producer: AIOKafkaProducer = request.app.state.kafka_producer
        if not producer:
            raise HTTPException(status_code=503, detail="Kafka producer not initialized")
        return producer
    except AttributeError:
        raise HTTPException(status_code=503, detail="Kafka service not available")