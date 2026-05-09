from uuid import UUID

from arq import ArqRedis
from fastapi import Depends, HTTPException, Request, status

from app.infrastructure.db.uow import UnitOfWork
from app.services.service import NotificationService


async def get_uow(request: Request) -> UnitOfWork:
    """Создает UnitOfWork с фабрикой сессий из app.state."""
    db_session_maker = getattr(request.app.state, "db_session_maker", None)
    if db_session_maker is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database session factory not available",
        )

    return UnitOfWork(db_session_maker)


def get_arq_pool(request: Request) -> ArqRedis | None:
    """Возвращает ARQ pool для постановки фоновых задач."""
    return getattr(request.app.state, "arq_pool", None)


def get_notification_service(
    uow: UnitOfWork = Depends(get_uow),
    arq_pool: ArqRedis | None = Depends(get_arq_pool),
) -> NotificationService:
    """Создает сервис уведомлений."""
    return NotificationService(
        unit_of_work=uow,
        arq_pool=arq_pool,
    )


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
