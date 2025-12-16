import jwt
from fastapi import Depends, status, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator
from uuid import UUID
from arq.connections import ArqRedis

from app import (
    repositories, 
    services,
    settings
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
    Декодирует JWT, валидирует подпись публичным ключом и возвращает userId.
    Далее перенести в API Gateway.
    """
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No access token provided")

    try:
        public_key = settings.settings.JWT.JWT_PUBLIC_KEY.replace("\\n", "\n")
        payload = jwt.decode(
            access_token,
            public_key,
            algorithms=[settings.settings.JWT.JWT_ALGORITHM],
            audience=settings.settings.JWT.JWT_AUDIENCE,
        )

        userId_str = payload.get("sub")
        if not userId_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing subject (userId)"
            )

        userId = UUID(userId_str)
        return userId

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Token has expired"
        )
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail=f"Could not validate credentials: {e}"
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid user ID format in token"
        )