from fastapi import Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis, ConnectionPool
from arq.connections import ArqRedis
from aiokafka import AIOKafkaProducer
from typing import AsyncGenerator

from app import settings
from app.services.classification_service import ClassificationService
from app.services.ml_service import modelManager

async def getDb(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """Обеспечивает асинхронный сеанс работы с базой данных из пула в app.state."""
    dbSessionMaker = request.app.state.dbSessionMaker
    if not dbSessionMaker:
        raise HTTPException(status_code=503, detail="Database session factory not available")
    async with dbSessionMaker() as session:
        yield session

async def getRedis(request: Request) -> AsyncGenerator[Redis, None]:
    """Обеспечивает подключение Redis из пула."""
    pool: ConnectionPool = request.app.state.redisPool
    redis = Redis(connection_pool=pool, decode_responses=True)
    try:
        yield redis
    finally:
        await redis.aclose()

async def createRedisPool() -> ConnectionPool:
    """Создает пул подключений Redis."""
    return ConnectionPool.from_url(settings.settings.ARQ.REDIS_URL, decode_responses=True)

async def closeRedisPool(pool: ConnectionPool):
    """Закрывает пул подключений Redis."""
    await pool.disconnect()

async def getArqPool(request: Request) -> AsyncGenerator[ArqRedis, None]:
    """Предоставляет пул Arq."""
    arqPool: ArqRedis = request.app.state.arqPool
    try:
        yield arqPool
    finally:
        pass

async def getKafkaProducer(request: Request) -> AIOKafkaProducer:
    """Зависимость для получения Kafka-продюсера."""
    kafkaProducer: AIOKafkaProducer = request.app.state.kafkaProducer
    if not kafkaProducer:
        raise HTTPException(status_code=503, detail="Kafka producer not initialized")
    return kafkaProducer

def getMlPipeline(request: Request) -> dict | None:
    """
    Извлекает актуальный ML-пайплайн из менеджера.
    """
    return modelManager.getPipeline()

async def getClassificationService(
    db: AsyncSession = Depends(getDb),
    redis: Redis = Depends(getRedis),
    mlPipeline: dict | None = Depends(getMlPipeline)
) -> ClassificationService:
    """
    Фабрика зависимостей.
    """
    return ClassificationService(db, redis, mlPipeline)