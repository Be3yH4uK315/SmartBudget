import ipaddress
from fastapi import Depends, Request, HTTPException
from redis.asyncio import Redis, ConnectionPool
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from typing import AsyncGenerator
from arq.connections import ArqRedis
from jwt import ExpiredSignatureError, InvalidSignatureError, decode, PyJWTError
import geoip2.database

from app import (
    models,
    settings,
    middleware,
    repositories
)

async def get_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """Обеспечивает асинхронный сеанс работы с базой данных из пула в app.state."""
    async_session_maker: async_sessionmaker[AsyncSession] = request.app.state.db_session_maker
    if not async_session_maker:
        middleware.logger.error("DB Session Maker not found in app.state.")
        raise HTTPException(status_code=500, detail="Database connection not available")

    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

def get_user_repository(db: AsyncSession = Depends(get_db)) -> repositories.UserRepository:
    """Провайдер для UserRepository."""
    return repositories.UserRepository(db)

def get_session_repository(db: AsyncSession = Depends(get_db)) -> repositories.SessionRepository:
    """Провайдер для SessionRepository."""
    return repositories.SessionRepository(db)

async def get_redis(request: Request) -> AsyncGenerator[Redis, None]:
    """Обеспечивает подключение Redis из пула."""
    pool: ConnectionPool = request.app.state.redis_pool
    redis = Redis(connection_pool=pool, decode_responses=True)
    try:
        yield redis
    finally:
        await redis.aclose()

async def create_redis_pool() -> ConnectionPool:
    """Создает пул подключений Redis."""
    return ConnectionPool.from_url(settings.settings.app.redis_url, decode_responses=True)

async def close_redis_pool(pool: ConnectionPool):
    """Закрывает пул подключений Redis."""
    await pool.disconnect()

async def get_arq_pool(request: Request) -> AsyncGenerator[ArqRedis, None]:
    """Предоставляет пул Arq."""
    arq_pool: ArqRedis = request.app.state.arq_pool
    try:
        yield arq_pool
    finally:
        pass

def get_geoip_reader(request: Request) -> geoip2.database.Reader:
    """Возвращает GeoIP reader, инициализированный при старте."""
    try:
        return request.app.state.geoip_reader
    except AttributeError:
        middleware.logger.error(
            "GeoIP reader not found in app.state. Make sure it is initialized in lifespan."
        )
        raise HTTPException(status_code=500, detail="GeoIP service not available")

def get_real_ip(request: Request) -> str:
    """Извлекает реальный IP-адрес из запроса, учитывая цепочку прокси."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        ips = [ip.strip() for ip in forwarded.split(",")]
        for ip in ips:
            try:
                addr = ipaddress.ip_address(ip)
                if not addr.is_private:
                    return ip
            except ValueError:
                middleware.logger.warning(f"Invalid IP in x-forwarded-for: {ip}")
        middleware.logger.warning(f"No valid public IP in x-forwarded-for: {forwarded}")
    client_host = request.client.host if request.client else "127.0.0.1"
    middleware.logger.debug(f"Falling back to client.host: {client_host}")
    return client_host

async def get_current_active_user(
    request: Request, db: AsyncSession = Depends(get_db)
) -> models.User:
    """Извлекает и проверяет текущего активного пользователя из токена."""
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(
            status_code=401, 
            detail="Not authenticated (missing token)"
        )
    try:
        payload = decode(
            access_token,
            settings.settings.jwt.jwt_public_key,
            algorithms=[settings.settings.jwt.jwt_algorithm],
            audience='smart-budget'
        )
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token (missing sub)")
        
        user_repo = repositories.UserRepository(db)
        user = await user_repo.get_by_id(UUID(user_id))
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="User inactive or not found")

        return user    
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except InvalidSignatureError:
        raise HTTPException(status_code=401, detail="Invalid token signature (Key mismatch)")
    except PyJWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token")
    except ValueError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token payload")

async def get_user_id_from_expired_token(request: Request) -> str | None:
    """
    Извлекает user_id из access_token, игнорируя срок его действия.
    Нужно для эндпоинта /logout.
    """
    access_token = request.cookies.get("access_token")
    if not access_token:
        return None
    try:
        payload = decode(
            access_token,
            settings.settings.jwt.jwt_public_key,
            algorithms=[settings.settings.jwt.jwt_algorithm],
            audience='smart-budget',
            options={"verify_exp": False}
        )
        user_id: str | None = payload.get("sub")
        return user_id
    except (PyJWTError, ValueError):
        middleware.logger.warning("Invalid token structure encountered during logout")
        return None
