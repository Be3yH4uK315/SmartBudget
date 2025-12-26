from fastapi import Depends, Request, HTTPException
from redis.asyncio import Redis, ConnectionPool
from typing import AsyncGenerator

from app import settings, unit_of_work
from app.services.classification_service import ClassificationService
from app.services.ml_service import modelManager
from app.services.rule_manager import ruleManager

async def get_uow(request: Request) -> AsyncGenerator[unit_of_work.UnitOfWork, None]:
    """Создает UnitOfWork с фабрикой сессий из app.state."""
    db_session_maker = request.app.state.db_session_maker
    if not db_session_maker:
        raise HTTPException(status_code=500, detail="Database session factory not available")
    yield unit_of_work.UnitOfWork(db_session_maker)

async def get_redis(request: Request) -> AsyncGenerator[Redis, None]:
    """Обеспечивает подключение Redis из пула."""
    pool: ConnectionPool = request.app.state.redis_pool
    client = Redis(connection_pool=pool, decode_responses=True)
    try:
        yield client
    finally:
        await client.aclose()

async def create_redis_pool() -> ConnectionPool:
    """Создает пул подключений Redis."""
    return ConnectionPool.from_url(settings.settings.ARQ.REDIS_URL, decode_responses=True)

async def close_redis_pool(pool: ConnectionPool) -> None:
    """Закрывает пул подключений Redis."""
    await pool.disconnect()

def get_ml_pipeline() -> dict | None:
    """Получает актуальный ML-пайплайн из менеджера."""
    return modelManager.get_pipeline()

def get_active_rules() -> list[dict]:
    """Зависимость для получения правил из памяти."""
    return ruleManager.get_rules()

async def get_classification_service(
    uow: unit_of_work.UnitOfWork = Depends(get_uow),
    redis: Redis = Depends(get_redis),
    pipeline: dict = Depends(get_ml_pipeline),
    rules: list[dict] = Depends(get_active_rules)
) -> ClassificationService:
    """Фабрика зависимостей для ClassificationService."""
    return ClassificationService(uow, redis, pipeline, rules)