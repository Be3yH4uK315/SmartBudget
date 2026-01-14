import ipaddress
from typing import AsyncGenerator
from uuid import UUID
from fastapi import Depends, Request, HTTPException, BackgroundTasks
from redis.asyncio import Redis, ConnectionPool
from arq.connections import ArqRedis

from app.core import exceptions
from app.domain.schemas.dtos import UserDTO
from app.infrastructure.db.uow import UnitOfWork
from app.services.session_service import SessionService
from app.services.notifier import AuthNotifier
from app.services.registration_service import RegistrationService
from app.services.login_service import LoginService
from app.services.password_service import PasswordService
from app.services.token_service import TokenService
from app.core.config import settings

async def get_uow(request: Request) -> UnitOfWork:
    """Создает UnitOfWork с фабрикой сессий из app.state."""
    db_session_maker = request.app.state.db_session_maker
    if not db_session_maker:
        raise HTTPException(status_code=500, detail="Database session factory not available")
    
    return UnitOfWork(db_session_maker)

async def get_redis(request: Request) -> AsyncGenerator[Redis, None]:
    """Обеспечивает подключение Redis из пула."""
    pool: ConnectionPool = request.app.state.redis_pool
    if not pool:
        raise HTTPException(status_code=500, detail="Redis pool not available")

    redis = Redis(connection_pool=pool, decode_responses=True)
    try:
        yield redis
    finally:
        await redis.aclose()

async def get_arq_pool(request: Request) -> AsyncGenerator[ArqRedis, None]:
    """Предоставляет пул Arq."""
    arq_pool: ArqRedis = request.app.state.arq_pool
    if not arq_pool:
        raise HTTPException(status_code=500, detail="ARQ pool not available")
    yield arq_pool

async def get_dadata_client(request: Request):
    """Предоставляет клиент DaData из state приложения."""
    client = getattr(request.app.state, "dadata_client", None)
    return client

def get_token_service() -> TokenService:
    return TokenService()

def get_auth_notifier(
    uow=Depends(get_uow),
    arq_pool=Depends(get_arq_pool)
) -> AuthNotifier:
    return AuthNotifier(uow=uow, arq_pool=arq_pool)

def get_session_service(
    uow=Depends(get_uow),
    redis=Depends(get_redis),
    token_service=Depends(get_token_service),
    notifier=Depends(get_auth_notifier)
) -> SessionService:
    return SessionService(
        uow=uow, 
        redis=redis, 
        token_service=token_service,
        notifier=notifier
    )

def get_registration_service(
    uow=Depends(get_uow),
    redis=Depends(get_redis),
    session_service=Depends(get_session_service),
    notifier=Depends(get_auth_notifier)
) -> RegistrationService:
    return RegistrationService(
        uow=uow,
        redis=redis,
        session_service=session_service,
        notifier=notifier
    )

def get_login_service(
    uow=Depends(get_uow),
    redis=Depends(get_redis),
    session_service=Depends(get_session_service),
    notifier=Depends(get_auth_notifier)
) -> LoginService:
    return LoginService(
        uow=uow,
        redis=redis,
        session_service=session_service,
        notifier=notifier
    )

def get_password_service(
    uow=Depends(get_uow),
    redis=Depends(get_redis),
    session_service=Depends(get_session_service),
    notifier=Depends(get_auth_notifier)
) -> PasswordService:
    return PasswordService(
        uow=uow,
        redis=redis,
        session_service=session_service,
        notifier=notifier
    )

async def create_redis_pool() -> ConnectionPool:
    """Создает пул подключений Redis."""
    return ConnectionPool.from_url(settings.ARQ.REDIS_URL, decode_responses=True)

async def close_redis_pool(pool: ConnectionPool) -> None:
    """Закрывает пул подключений Redis."""
    await pool.disconnect()

def get_real_ip(request: Request) -> str:
    """Извлекает реальный IP-адрес из запроса, учитывая цепочку прокси."""
    if settings.APP.ENV in ('prod', 'stage'): 
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            first_ip = forwarded.split(",")[0].strip()
            try:
                ipaddress.ip_address(first_ip)
                return first_ip
            except ValueError:
                pass
    
    return request.client.host if request.client else "127.0.0.1"

async def get_current_active_user(
    request: Request,
    background_tasks: BackgroundTasks,
    session_service: SessionService = Depends(get_session_service)
) -> UserDTO:
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        user_dto, session_id_str = await session_service.get_user_and_session_id(access_token)
        if session_id_str:
            background_tasks.add_task(session_service.update_activity, UUID(session_id_str))
        return user_dto
    except (exceptions.AuthServiceError, exceptions.InvalidTokenError) as e:
        raise HTTPException(status_code=401, detail=str(e))
    except exceptions.UserInactiveError:
        raise HTTPException(status_code=403, detail="User is inactive")
    except exceptions.UserNotFoundError:
        raise HTTPException(status_code=401, detail="User not found")

async def get_user_id_from_expired_token(
    request: Request,
    token_service: TokenService = Depends(get_token_service)
) -> str | None:
    """Извлекает userId из access_token, игнорируя срок его действия."""
    token = request.cookies.get("access_token")
    if not token:
        return None
    return token_service.get_user_id_from_expired_token(token)
