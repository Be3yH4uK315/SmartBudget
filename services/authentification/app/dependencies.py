from fastapi import Depends, Request, HTTPException
from redis.asyncio import Redis, ConnectionPool
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from typing import AsyncGenerator
from arq.connections import ArqRedis
from jwt import ExpiredSignatureError, InvalidSignatureError, decode, PyJWTError
import geoip2.database

from .settings import settings
from .middleware import logger
from .models import User

# --- DB ---
engine = create_async_engine(settings.db_url)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session

# --- Redis ---
async def get_redis(request: Request) -> AsyncGenerator[Redis, None]:
    pool: ConnectionPool = request.app.state.redis_pool
    redis = Redis(connection_pool=pool, decode_responses=True)
    try:
        yield redis
    finally:
        await redis.aclose()

async def create_redis_pool() -> ConnectionPool:
    return ConnectionPool.from_url(settings.redis_url, decode_responses=True)

async def close_redis_pool(pool: ConnectionPool):
    await pool.disconnect()

# --- Arq ---
async def get_arq_pool(request: Request) -> AsyncGenerator[ArqRedis, None]:
    arq_pool: ArqRedis = request.app.state.arq_pool
    try:
        yield arq_pool
    finally:
        pass

def get_geoip_reader(request: Request) -> geoip2.database.Reader:
    """
    Возвращает GeoIP reader, инициализированный при старте.
    """
    try:
        return request.app.state.geoip_reader
    except AttributeError:
        logger.error("GeoIP reader not found in app.state. Make sure it is initialized in lifespan.")
        raise HTTPException(status_code=500, detail="GeoIP service not available")

def get_real_ip(request: Request) -> str:
    if "x-forwarded-for" in request.headers:
        return request.headers["x-forwarded-for"].split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"

async def get_current_user_id(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> str:
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(
            status_code=401, 
            detail="Not authenticated (missing token)"
        )
    try:
        payload = decode(
            access_token,
            settings.jwt_public_key,
            algorithms=[settings.jwt_algorithm],
            audience='smart-budget'
        )
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token (missing sub)")
        
        try:
            user = await db.get(User, UUID(user_id))
            if not user or not user.is_active:
                raise HTTPException(status_code=401, detail="User inactive or not found")
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid token payload")

        return user_id
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except InvalidSignatureError:
        raise HTTPException(status_code=401, detail="Invalid token signature (Key mismatch)")
    except PyJWTError as e:
        raise HTTPException(status_code=401, detail="Invalid token")