from collections.abc import AsyncGenerator
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from redis.asyncio import ConnectionPool, Redis

from app.infrastructure.db.uow import UnitOfWork
from app.services.classification.rules import ruleManager
from app.services.classification.service import ClassificationService
from app.services.ml.manager import modelManager


async def get_uow(request: Request) -> AsyncGenerator[UnitOfWork, None]:
    """Создает UnitOfWork с фабрикой сессий из app.state."""
    db_session_maker = getattr(request.app.state, "db_session_maker", None)
    if db_session_maker is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="DB session factory missing",
        )

    yield UnitOfWork(db_session_maker)


async def get_redis(request: Request) -> AsyncGenerator[Redis, None]:
    """Создает Redis client на основе общего connection pool."""
    pool: ConnectionPool | None = getattr(request.app.state, "redis_pool", None)
    if pool is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Redis pool not initialized",
        )

    client = Redis(connection_pool=pool)

    try:
        yield client
    finally:
        await client.aclose()


def get_ml_pipeline() -> dict | None:
    """Возвращает текущий ML pipeline из singleton manager-а."""
    return modelManager.get_pipeline()


def get_classification_rules() -> list[dict]:
    """Возвращает текущие правила классификации из singleton manager-а."""
    return ruleManager.get_rules()


async def get_current_user_id(request: Request) -> UUID:
    """Извлекает user_id из X-User-Id, который устанавливает API Gateway."""
    user_id = request.headers.get("X-User-Id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID header missing",
        )

    try:
        return UUID(user_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid User ID format",
        ) from exc


async def get_classification_service(
    uow: UnitOfWork = Depends(get_uow),
    redis: Redis = Depends(get_redis),
    pipeline: dict | None = Depends(get_ml_pipeline),
    rules: list[dict] = Depends(get_classification_rules),
) -> ClassificationService:
    """Создает ClassificationService."""
    return ClassificationService(uow, redis, pipeline, rules)
