from fastapi import Depends, status, HTTPException, Request
from typing import AsyncGenerator
from uuid import UUID
from arq.connections import ArqRedis

from app import (
    services, 
    unit_of_work
)

async def get_uow(request: Request) -> AsyncGenerator[unit_of_work.UnitOfWork, None]:
    """Создает UnitOfWork с фабрикой сессий из app.state."""
    db_session_maker = request.app.state.db_session_maker
    if not db_session_maker:
        raise HTTPException(status_code=500, detail="Database session factory not available")
    
    uow = unit_of_work.UnitOfWork(db_session_maker)
    yield uow

async def get_arq_pool(request: Request) -> AsyncGenerator[ArqRedis, None]:
    """Предоставляет пул Arq."""
    arq_pool: ArqRedis = request.app.state.arq_pool
    if not arq_pool:
         raise HTTPException(status_code=500, detail="Redis ARQ pool not available")
    yield arq_pool

def get_goal_service(
    uow: unit_of_work.UnitOfWork = Depends(get_uow),
) -> services.GoalService:
    return services.GoalService(uow)

async def get_current_user_id(request: Request) -> UUID:
    """
    Извлекает user_id из заголовка X-User-Id, который устанавливает API Gateway.
    """
    user_id = request.headers.get("X-User-Id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID header missing"
        )
    try:
        return UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid User ID format"
        )