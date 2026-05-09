import ipaddress
from collections.abc import AsyncGenerator
from typing import Any
from uuid import UUID

from arq.connections import ArqRedis
from fastapi import BackgroundTasks, Depends, HTTPException, Request
from redis.asyncio import ConnectionPool, Redis

from app.core import exceptions
from app.core.config import settings
from app.domain.schemas.dtos import UserDTO
from app.infrastructure.db.uow import UnitOfWork
from app.services.login_service import LoginService
from app.services.notifier import AuthNotifier
from app.services.password_service import PasswordService
from app.services.profile_service import ProfileService
from app.services.registration_service import RegistrationService
from app.services.session_service import SessionService
from app.services.token_service import TokenService


async def get_uow(request: Request) -> UnitOfWork:
    """Создает UnitOfWork с фабрикой сессий из app.state."""
    db_session_maker = getattr(request.app.state, "db_session_maker", None)
    if db_session_maker is None:
        raise HTTPException(
            status_code=500,
            detail="Database session factory not available",
        )

    return UnitOfWork(db_session_maker)


async def get_redis(request: Request) -> AsyncGenerator[Redis, None]:
    """Предоставляет Redis-клиент из общего пула подключений."""
    pool: ConnectionPool | None = getattr(request.app.state, "redis_pool", None)
    if pool is None:
        raise HTTPException(
            status_code=500,
            detail="Redis pool not available",
        )

    redis = Redis(connection_pool=pool, decode_responses=True)
    try:
        yield redis
    finally:
        await redis.aclose()


async def get_arq_pool(request: Request) -> ArqRedis:
    """Предоставляет пул ARQ из app.state."""
    arq_pool: ArqRedis | None = getattr(request.app.state, "arq_pool", None)
    if arq_pool is None:
        raise HTTPException(
            status_code=500,
            detail="ARQ pool not available",
        )

    return arq_pool


async def get_dadata_client(request: Request) -> Any | None:
    """Предоставляет клиент DaData из app.state, если он был инициализирован."""
    return getattr(request.app.state, "dadata_client", None)


def get_token_service() -> TokenService:
    """Создает сервис токенов."""
    return TokenService()


def get_auth_notifier(
    uow: UnitOfWork = Depends(get_uow),
    arq_pool: ArqRedis = Depends(get_arq_pool),
) -> AuthNotifier:
    """Создает сервис уведомлений аутентификации."""
    return AuthNotifier(
        uow=uow,
        arq_pool=arq_pool,
    )


def get_session_service(
    uow: UnitOfWork = Depends(get_uow),
    redis: Redis = Depends(get_redis),
    token_service: TokenService = Depends(get_token_service),
    notifier: AuthNotifier = Depends(get_auth_notifier),
) -> SessionService:
    """Создает сервис управления сессиями."""
    return SessionService(
        uow=uow,
        redis=redis,
        token_service=token_service,
        notifier=notifier,
    )


def get_registration_service(
    uow: UnitOfWork = Depends(get_uow),
    redis: Redis = Depends(get_redis),
    session_service: SessionService = Depends(get_session_service),
    notifier: AuthNotifier = Depends(get_auth_notifier),
) -> RegistrationService:
    """Создает сервис регистрации."""
    return RegistrationService(
        uow=uow,
        redis=redis,
        session_service=session_service,
        notifier=notifier,
    )


def get_login_service(
    uow: UnitOfWork = Depends(get_uow),
    redis: Redis = Depends(get_redis),
    session_service: SessionService = Depends(get_session_service),
    notifier: AuthNotifier = Depends(get_auth_notifier),
) -> LoginService:
    """Создает сервис аутентификации пользователя."""
    return LoginService(
        uow=uow,
        redis=redis,
        session_service=session_service,
        notifier=notifier,
    )


def get_password_service(
    uow: UnitOfWork = Depends(get_uow),
    redis: Redis = Depends(get_redis),
    session_service: SessionService = Depends(get_session_service),
    notifier: AuthNotifier = Depends(get_auth_notifier),
) -> PasswordService:
    """Создает сервис управления паролями."""
    return PasswordService(
        uow=uow,
        redis=redis,
        session_service=session_service,
        notifier=notifier,
    )


def get_profile_service(
    uow: UnitOfWork = Depends(get_uow),
    redis: Redis = Depends(get_redis),
    session_service: SessionService = Depends(get_session_service),
    notifier: AuthNotifier = Depends(get_auth_notifier),
) -> ProfileService:
    """Создает сервис управления профилем пользователя."""
    return ProfileService(
        uow=uow,
        redis=redis,
        session_service=session_service,
        notifier=notifier,
    )


async def create_redis_pool() -> ConnectionPool:
    """Создает пул подключений Redis."""
    return ConnectionPool.from_url(
        settings.ARQ.REDIS_URL,
        decode_responses=True,
    )


async def close_redis_pool(pool: ConnectionPool) -> None:
    """Закрывает пул подключений Redis."""
    await pool.disconnect()


def get_real_ip(request: Request) -> str:
    """Извлекает реальный IP-адрес запроса с учетом доверенного прокси."""
    if settings.APP.ENV in ("prod", "stage"):
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
    session_service: SessionService = Depends(get_session_service),
) -> UserDTO:
    """Извлекает текущего активного пользователя из access token в cookies."""
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
        )

    try:
        user_dto, session_id = await session_service.get_user_and_session_id(
            access_token,
        )
        background_tasks.add_task(
            session_service.update_activity,
            UUID(session_id),
        )

        return user_dto

    except exceptions.UserInactiveError as exc:
        raise HTTPException(
            status_code=403,
            detail="User is inactive",
        ) from exc
    except exceptions.UserNotFoundError as exc:
        raise HTTPException(
            status_code=401,
            detail="User not found",
        ) from exc
    except (exceptions.AuthServiceError, exceptions.InvalidTokenError) as exc:
        raise HTTPException(
            status_code=401,
            detail=str(exc),
        ) from exc


async def get_user_id_from_expired_token(
    request: Request,
    token_service: TokenService = Depends(get_token_service),
) -> str | None:
    """Извлекает user_id из access token, игнорируя срок его действия."""
    token = request.cookies.get("access_token")
    if not token:
        return None

    return await token_service.get_user_id_from_expired_token(token)
