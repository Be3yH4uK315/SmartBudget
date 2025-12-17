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
    """Получает dbSessionMaker из app.state и предоставляет сессию."""
    dbSessionMaker = request.app.state.dbSessionMaker
    if not dbSessionMaker:
        raise HTTPException(status_code=500, detail="Database session factory not available")
        
    async with dbSessionMaker() as session:
        yield session

def getGoalRepository(db: AsyncSession = Depends(getDb)) -> repositories.GoalRepository:
    """Провайдер для GoalRepository."""
    return repositories.GoalRepository(db)

async def getArqPool(request: Request) -> AsyncGenerator[ArqRedis, None]:
    """Предоставляет пул Arq из app.state."""
    arqPool: ArqRedis = request.app.state.arqPool
    try:
        yield arqPool
    finally:
        pass

def getGoalService(
    repository: repositories.GoalRepository = Depends(getGoalRepository),
) -> services.GoalService:
    """Провайдер для GoalService."""
    return services.GoalService(repository)

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