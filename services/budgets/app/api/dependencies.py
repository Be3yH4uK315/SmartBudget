from uuid import UUID

from fastapi import Depends, HTTPException, Request, status

from app.infrastructure.db.uow import UnitOfWork
from app.services.service import BudgetService


async def get_uow(request: Request) -> UnitOfWork:
    """Создает UnitOfWork с фабрикой сессий из app.state."""
    db_session_maker = request.app.state.db_session_maker
    if not db_session_maker:
        raise HTTPException(
            status_code=500,
            detail="Database session factory not available",
        )
    return UnitOfWork(db_session_maker)


def get_budget_service(uow: UnitOfWork = Depends(get_uow)) -> BudgetService:
    """Создает сервис бюджетов."""
    return BudgetService(uow)


async def get_current_user_id(request: Request) -> UUID:
    """Извлекает user_id из заголовка X-User-Id, который устанавливает API Gateway."""
    user_id = request.headers.get("X-User-Id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID header missing",
        )
    try:
        return UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid User ID format",
        )
