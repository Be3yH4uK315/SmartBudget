from fastapi import Depends, status, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator
from uuid import UUID
from arq.connections import ArqRedis

from app import (
    repositories, 
    services,
    settings
)

security = HTTPBearer()

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

async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> UUID:
    """
    Декодирует JWT, валидирует подпись публичным ключом и возвращает user_id.
    Далее перенести в API Gateway.
    """
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.settings.jwt.jwt_public_key,
            algorithms=[settings.settings.jwt.jwt_algorithm],
            audience=settings.settings.jwt.jwt_audience,
        )
        
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Token missing subject (user_id)"
            )
            
        return UUID(user_id_str)

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