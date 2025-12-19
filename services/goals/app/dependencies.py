from fastapi import Depends, status, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator
from uuid import UUID
from arq.connections import ArqRedis

from app import (
    repositories, 
    services
)

async def get_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """Получает db_session_maker из app.state и предоставляет сессию."""
    db_session_maker = request.app.state.dbSessionMaker
    if not db_session_maker:
        raise HTTPException(status_code=500, detail="Database session factory not available")
        
    async with db_session_maker() as session:
        yield session

def get_goal_repository(db: AsyncSession = Depends(get_db)) -> repositories.GoalRepository:
    """Провайдер для GoalRepository."""
    return repositories.GoalRepository(db)

async def get_arq_pool(request: Request) -> AsyncGenerator[ArqRedis, None]:
    """Предоставляет пул Arq из app.state."""
    arq_pool: ArqRedis = request.app.state.arqPool
    try:
        yield arq_pool
    finally:
        pass

def get_goal_service(
    repository: repositories.GoalRepository = Depends(get_goal_repository),
) -> services.GoalService:
    """Провайдер для GoalService."""
    return services.GoalService(repository)

async def get_current_user_id(request: Request) -> UUID:
    """
    Извлекает user_id из заголовка X-User-Id, который устанавливает API Gateway.
    """
    user_id = request.headers.get("X-User-Id")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID header missing. Access denied."
        )
    try:
        return UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid User ID format"
        )