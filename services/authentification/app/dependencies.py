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

async def getDb(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """Обеспечивает асинхронный сеанс работы с базой данных из пула в app.state."""
    dbSessionMaker: async_sessionmaker[AsyncSession] = request.app.state.dbSessionMaker
    if not dbSessionMaker:
        middleware.logger.error("DB Session Maker not found in app.state.")
        raise HTTPException(status_code=500, detail="Database connection not available")

    async with dbSessionMaker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

def getUserRepository(db: AsyncSession = Depends(getDb)) -> repositories.UserRepository:
    """Провайдер для UserRepository."""
    return repositories.UserRepository(db)

def getSessionRepository(db: AsyncSession = Depends(getDb)) -> repositories.SessionRepository:
    """Провайдер для SessionRepository."""
    return repositories.SessionRepository(db)

async def getRedis(request: Request) -> AsyncGenerator[Redis, None]:
    """Обеспечивает подключение Redis из пула."""
    pool: ConnectionPool = request.app.state.redisPool
    redis = Redis(connection_pool=pool, decode_responses=True)
    try:
        yield redis
    finally:
        await redis.aclose()

async def createRedisPool() -> ConnectionPool:
    """Создает пул подключений Redis."""
    return ConnectionPool.from_url(settings.settings.ARQ.REDIS_URL, decode_responses=True)

async def closeRedisPool(pool: ConnectionPool):
    """Закрывает пул подключений Redis."""
    await pool.disconnect()

async def getArqPool(request: Request) -> AsyncGenerator[ArqRedis, None]:
    """Предоставляет пул Arq."""
    arqPool: ArqRedis = request.app.state.arqPool
    try:
        yield arqPool
    finally:
        pass

def getGeoipReader(request: Request) -> geoip2.database.Reader:
    """Возвращает GeoIP reader, инициализированный при старте."""
    try:
        return request.app.state.geoIpReader
    except AttributeError:
        middleware.logger.error(
            "GeoIP reader not found in app.state. Make sure it is initialized in lifespan."
        )
        raise HTTPException(status_code=500, detail="GeoIP service not available")

def getRealIp(request: Request) -> str:
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
    clientHost = request.client.host if request.client else "127.0.0.1"
    middleware.logger.debug(f"Falling back to client.host: {clientHost}")
    return clientHost

async def getCurrentActiveUser(
    request: Request, db: AsyncSession = Depends(getDb)
) -> models.User:
    """Извлекает и проверяет текущего активного пользователя из токена."""
    accessToken = request.cookies.get("access_token")
    if not accessToken:
        raise HTTPException(
            status_code=401, 
            detail="Not authenticated (missing token)"
        )
    try:
        payload = decode(
            accessToken,
            settings.settings.JWT.JWT_PUBLIC_KEY,
            algorithms=[settings.settings.JWT.JWT_ALGORITHM],
            audience='smart-budget'
        )
        userId: str | None = payload.get("sub")
        if userId is None:
            raise HTTPException(status_code=401, detail="Invalid token (missing sub)")
        
        UserRepository = repositories.UserRepository(db)
        user = await UserRepository.getById(UUID(userId))
        if not user or not user.isActive:
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

async def getUserIdFromExpiredToken(request: Request) -> str | None:
    """
    Извлекает userId из access_token, игнорируя срок его действия.
    Нужно для эндпоинта /logout.
    """
    accessToken = request.cookies.get("access_token")
    if not accessToken:
        return None
    try:
        payload = decode(
            accessToken,
            settings.settings.JWT.JWT_PUBLIC_KEY,
            algorithms=[settings.settings.JWT.JWT_ALGORITHM],
            audience='smart-budget',
            options={"verify_exp": False}
        )
        userId: str | None = payload.get("sub")
        return userId
    except (PyJWTError, ValueError):
        middleware.logger.warning("Invalid token structure encountered during logout")
        return None