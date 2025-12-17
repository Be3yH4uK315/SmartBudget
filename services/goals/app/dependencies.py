from fastapi import Depends, status, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator
from uuid import UUID
from arq.connections import ArqRedis

from app import (
    repositories, 
    services
)

async def getDb(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """Получает session_maker из app.state и предоставляет сессию."""
    session_maker = request.app.state.async_session_maker
    if not session_maker:
        raise HTTPException(status_code=500, detail="Database session factory not available")
        
    async with session_maker() as session:
        yield session

def getGoalRepository(db: AsyncSession = Depends(getDb)) -> repositories.GoalRepository:
    """Провайдер для GoalRepository."""
    return repositories.GoalRepository(db)

async def getArqPool(request: Request) -> AsyncGenerator[ArqRedis, None]:
    """Предоставляет пул Arq из app.state."""
    arq_pool: ArqRedis = request.app.state.arq_pool
    try:
        yield arq_pool
    finally:
        pass

def getGoalService(
    repo: repositories.GoalRepository = Depends(getGoalRepository),
) -> services.GoalService:
    """Провайдер для GoalService."""
    return services.GoalService(repo)

async def getCurrentUserId(request: Request) -> UUID:
    """
    Извлекает userId из заголовка X-User-Id, который устанавливает API Gateway.
    """
    userId = request.headers.get("X-User-Id")
    
    if not userId:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID header missing. Access denied."
        )
    try:
        return UUID(userId)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid User ID format"
        )