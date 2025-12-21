import ipaddress
from typing import AsyncGenerator
from uuid import UUID
from fastapi import Depends, Request, HTTPException
from jwt import ExpiredSignatureError, InvalidSignatureError, PyJWTError, decode
from redis.asyncio import Redis, ConnectionPool
from arq.connections import ArqRedis
import geoip2.database

from app import middleware, models, services, settings, unit_of_work

async def get_uow(request: Request) -> AsyncGenerator[unit_of_work.UnitOfWork, None]:
    """Создает UnitOfWork с фабрикой сессий из app.state."""
    db_session_maker = request.app.state.db_session_maker
    if not db_session_maker:
        raise HTTPException(status_code=500, detail="Database session factory not available")
    
    uow = unit_of_work.UnitOfWork(db_session_maker)
    yield uow

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

def get_geoip_reader(request: Request) -> geoip2.database.Reader:
    """Возвращает GeoIP reader, инициализированный при старте."""
    reader = getattr(request.app.state, "geoip_reader", None)
    if not reader:
        raise HTTPException(status_code=500, detail="GeoIP reader not available")
    return reader

def get_auth_service(
    uow=Depends(get_uow),
    redis=Depends(get_redis),
    arq_pool=Depends(get_arq_pool),
    geoip=Depends(get_geoip_reader),
) -> services.AuthService:
    return services.AuthService(
        uow=uow,
        redis=redis,
        arq_pool=arq_pool,
        geoip_reader=geoip,
    )

async def create_redis_pool() -> ConnectionPool:
    """Создает пул подключений Redis."""
    return ConnectionPool.from_url(settings.settings.ARQ.REDIS_URL, decode_responses=True)

async def close_redis_pool(pool: ConnectionPool) -> None:
    """Закрывает пул подключений Redis."""
    await pool.disconnect()

def get_real_ip(request: Request) -> str:
    """Извлекает реальный IP-адрес из запроса, учитывая цепочку прокси."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        for ip in (x.strip() for x in forwarded.split(",")):
            try:
                addr = ipaddress.ip_address(ip)
                if not addr.is_private:
                    return ip
            except ValueError:
                middleware.logger.warning(f"Invalid IP in x-forwarded-for: {ip}")

    return request.client.host if request.client else "127.0.0.1"

async def get_current_active_user(
    request: Request,
    uow: unit_of_work.UnitOfWork = Depends(get_uow),
) -> models.User:
    """Извлекает и проверяет текущего активного пользователя из токена."""
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = decode(
            access_token,
            settings.settings.JWT.JWT_PUBLIC_KEY,
            algorithms=[settings.settings.JWT.JWT_ALGORITHM],
            audience="smart-budget",
        )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = await uow.users.get_by_id(UUID(user_id))
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="User inactive or not found")

        return user

    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except InvalidSignatureError:
        raise HTTPException(status_code=401, detail="Invalid token signature")
    except PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid token payload")

async def get_user_id_from_expired_token(request: Request) -> str | None:
    """
    Извлекает userId из access_token, игнорируя срок его действия.
    Нужно для эндпоинта /logout.
    """
    token = request.cookies.get("access_token")
    if not token:
        return None

    try:
        payload = decode(
            token,
            settings.settings.JWT.JWT_PUBLIC_KEY,
            algorithms=[settings.settings.JWT.JWT_ALGORITHM],
            audience="smart-budget",
            options={"verify_exp": False},
        )
        return payload.get("sub")
    except (PyJWTError, ValueError):
        middleware.logger.warning("Invalid token during logout")
        return None