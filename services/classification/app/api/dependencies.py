from fastapi import Depends, Request, HTTPException
from redis.asyncio import Redis, ConnectionPool
from typing import AsyncGenerator

from app.infrastructure.db.uow import UnitOfWork
from app.services.classification.service import ClassificationService
from app.services.ml.manager import modelManager
from app.services.classification.rules import ruleManager

async def get_uow(request: Request) -> AsyncGenerator[UnitOfWork, None]:
    """DI для UnitOfWork."""
    db_session_maker = request.app.state.db_session_maker
    if not db_session_maker:
        raise HTTPException(status_code=500, detail="DB session factory missing")
    yield UnitOfWork(db_session_maker)

async def get_redis(request: Request) -> AsyncGenerator[Redis, None]:
    """DI для Redis клиента."""
    pool: ConnectionPool = getattr(request.app.state, "redis_pool", None)
    if not pool:
        raise HTTPException(status_code=500, detail="Redis pool not initialized")
    client = Redis(connection_pool=pool)
    try:
        yield client
    finally:
        await client.aclose()

def get_ml_pipeline() -> dict | None:
    """DI для ML пайплайна (из Singleton)."""
    return modelManager.get_pipeline()

def get_classification_rules() -> list[dict]:
    """DI для правил классификации (из Singleton)."""
    return ruleManager.get_rules()

async def get_classification_service(
    uow: UnitOfWork = Depends(get_uow),
    redis: Redis = Depends(get_redis),
    pipeline: dict = Depends(get_ml_pipeline),
    rules: list[dict] = Depends(get_classification_rules)
) -> ClassificationService:
    """DI для ClassificationService."""
    return ClassificationService(uow, redis, pipeline, rules)