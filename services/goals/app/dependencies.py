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

async def get_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """Получает session_maker из app.state и предоставляет сессию."""
    session_maker = request.app.state.async_session_maker
    if not session_maker:
        raise HTTPException(status_code=500, detail="Database session factory not available")
        
    async with session_maker() as session:
        yield session

def get_goal_repository(db: AsyncSession = Depends(get_db)) -> repositories.GoalRepository:
    """Провайдер для GoalRepository."""
    return repositories.GoalRepository(db)

async def get_arq_pool(request: Request) -> AsyncGenerator[ArqRedis, None]:
    """Предоставляет пул Arq из app.state."""
    arq_pool: ArqRedis = request.app.state.arq_pool
    try:
        yield arq_pool
    finally:
        pass

def get_goal_service(
    repo: repositories.GoalRepository = Depends(get_goal_repository),
) -> services.GoalService:
    """Провайдер для GoalService."""
    return services.GoalService(repo)

async def get_current_user_id(request: Request) -> UUID:
    """
    Декодирует JWT, валидирует подпись публичным ключом и возвращает user_id.
    Далее перенести в API Gateway.
    """
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No access token provided")

    try:
        public_key = settings.settings.jwt.jwt_public_key.replace("\\n", "\n")
        payload = jwt.decode(
            access_token,
            public_key,
            algorithms=[settings.settings.jwt.jwt_algorithm],
            audience=settings.settings.jwt.jwt_audience,
        )

        user_id_str = payload.get("sub")
        if not user_id_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing subject (user_id)"
            )

        user_id = UUID(user_id_str)
        return user_id

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