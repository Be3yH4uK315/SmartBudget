from datetime import datetime, timedelta, timezone
import ipaddress
from typing import AsyncGenerator
from uuid import UUID
from fastapi import Depends, Request, HTTPException
from jwt import ExpiredSignatureError, InvalidSignatureError, PyJWTError, decode
import orjson
from redis.asyncio import Redis, ConnectionPool
from arq.connections import ArqRedis

from app.api import middleware
from app.infrastructure.db import models, uow as unit_of_work
from app.services import service as services 
from app.core.config import settings
from app.utils import redis_keys, serialization

async def get_uow(request: Request) -> unit_of_work.UnitOfWork:
    """Создает UnitOfWork с фабрикой сессий из app.state."""
    db_session_maker = request.app.state.db_session_maker
    if not db_session_maker:
        raise HTTPException(status_code=500, detail="Database session factory not available")
    
    return unit_of_work.UnitOfWork(db_session_maker)

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

def get_auth_service(
    uow=Depends(get_uow),
    redis=Depends(get_redis),
    arq_pool=Depends(get_arq_pool),
    dadata_client=Depends(get_dadata_client)
) -> services.AuthService:
    return services.AuthService(
        uow=uow,
        redis=redis,
        arq_pool=arq_pool,
        dadata_client=dadata_client
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
    uow: unit_of_work.UnitOfWork = Depends(get_uow),
    redis: Redis = Depends(get_redis)
) -> models.User:
    """
    Извлекает и проверяет текущего активного пользователя из токена. 
    Обновляет последнюю активность сессии.
    """
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = decode(
            access_token,
            settings.JWT.JWT_PUBLIC_KEY,
            algorithms=[settings.JWT.JWT_ALGORITHM],
            audience="smart-budget",
        )
        user_id_str = payload.get("sub")
        session_id_str = payload.get("sid")

        if not user_id_str or not session_id_str:
            raise HTTPException(status_code=401, detail="Invalid token structure")
        
        user_uuid = UUID(user_id_str)
        session_uuid = UUID(session_id_str)

        session_key = redis_keys.get_session_key(session_id_str)
        session_is_active_in_cache = await redis.exists(session_key)
        
        user = None

        if not session_is_active_in_cache:
            db_session = await uow.sessions.get_active_by_id(session_uuid)
            
            if not db_session:
                raise HTTPException(status_code=401, detail="Session expired or revoked")
            
            user = await uow.users.get_by_id(user_uuid)
            if not user or not user.is_active:
                raise HTTPException(status_code=401, detail="User inactive or not found")

            session_data = {
                "user_id": str(user.user_id),
                "role": user.role,
                "is_active": user.is_active,
                "session_id": str(db_session.session_id)
            }
            await redis.set(
                session_key, 
                serialization.to_json_str(session_data), 
                ex=timedelta(days=30)
            )

        if not user:
            cache_key = f"user:{user_id_str}"
            cached_data = await redis.get(cache_key)
            
            if cached_data:
                try:
                    data = orjson.loads(cached_data)
                    user = models.User(**data)
                    if isinstance(user.user_id, str): 
                        user.user_id = UUID(user.user_id)
                except Exception:
                    pass

            if not user:
                user = await uow.users.get_by_id(user_uuid)
                if not user:
                    raise HTTPException(status_code=401, detail="User not found")
                
                user_dict = {
                    c.name: getattr(user, c.name) 
                    for c in user.__table__.columns 
                    if c.name != "password_hash"
                }
                await redis.set(cache_key, serialization.to_json_str(user_dict), ex=60)

        if not user.is_active:
             raise HTTPException(status_code=401, detail="User inactive")

        try:
            throttle_key = f"session:activity_throttle:{session_id_str}"
            should_update = await redis.set(throttle_key, "1", ex=300, nx=True)
            
            if should_update:
                async with uow:
                    await uow.sessions.update_last_activity(
                        session_uuid, 
                        datetime.now(timezone.utc)
                    )
        except Exception as e:
            middleware.logger.error(f"Failed to update session activity: {e}")

        return user

    except (ExpiredSignatureError, InvalidSignatureError, PyJWTError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token")

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
            settings.JWT.JWT_PUBLIC_KEY,
            algorithms=[settings.JWT.JWT_ALGORITHM],
            audience="smart-budget",
            options={"verify_exp": False},
        )
        return payload.get("sub")
    except (PyJWTError, ValueError):
        middleware.logger.warning("Invalid token during logout")
        return None
