from fastapi import Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis, ConnectionPool
from arq.connections import ArqRedis
from aiokafka import AIOKafkaProducer
from typing import AsyncGenerator

from app import settings
from app.services.classification_service import ClassificationService
from app.services.ml_service import model_manager

async def get_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """Обеспечивает асинхронный сеанс работы с базой данных из пула в app.state."""
    session_maker = request.app.state.async_session_maker
    if not session_maker:
        raise HTTPException(status_code=503, detail="Database session factory not available")
    async with session_maker() as session:
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
    return ConnectionPool.from_url(settings.settings.redis.redis_url, decode_responses=True)

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
    producer: AIOKafkaProducer = request.app.state.kafka_producer
    if not producer:
        raise HTTPException(status_code=503, detail="Kafka producer not initialized")
    return producer

def get_ml_pipeline(request: Request) -> dict | None:
    """
    Извлекает актуальный ML-пайплайн из менеджера.
    """
    return model_manager.get_pipeline()

async def get_classification_service(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    ml_pipeline: dict | None = Depends(get_ml_pipeline)
) -> ClassificationService:
    """
    Фабрика зависимостей.
    """
    return ClassificationService(db, redis, ml_pipeline)