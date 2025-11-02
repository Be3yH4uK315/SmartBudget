from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from contextlib import asynccontextmanager
from redis.asyncio import Redis
from app.middleware import error_middleware, setup_logging
from app.routers.auth import router as auth_router
from app.dependencies import create_redis_pool, close_redis_pool
from fastapi_limiter import FastAPILimiter
from arq import create_pool
from arq.connections import RedisSettings
from app.settings import settings
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import geoip2.database
from app.middleware import logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    
    try:
        geoip_reader = geoip2.database.Reader(settings.geoip_db_path)
        app.state.geoip_reader = geoip_reader
        logger.info(f"GeoIP DB uploaded from {settings.geoip_db_path}")
    except FileNotFoundError:
        logger.error(f"GeoIP DB not found on the way: {settings.geoip_db_path}. Geolocation service will not work.")
        app.state.geoip_reader = None
    except Exception as e:
        logger.error(f"Error when uploading GeoIP DB: {e}")
        app.state.geoip_reader = None

    redis_pool = await create_redis_pool()
    app.state.redis_pool = redis_pool
    redis_limiter = Redis(connection_pool=redis_pool)
    await FastAPILimiter.init(redis_limiter)
    arq_redis_settings = RedisSettings.from_dsn(settings.redis_url)
    arq_redis_settings.queue_name = settings.arq_queue_name
    arq_pool = await create_pool(arq_redis_settings)
    app.state.arq_pool = arq_pool

    yield
    
    if hasattr(app.state, "geoip_reader") and app.state.geoip_reader:
        app.state.geoip_reader.close()
        logger.info("GeoIP DB Reader is closed.")
        del app.state.geoip_reader

    await FastAPILimiter.close()
    await close_redis_pool(redis_pool)
    if arq_pool:
        await arq_pool.close()
    if hasattr(app.state, "redis_pool"):
        del app.state.redis_pool
    if hasattr(app.state, "arq_pool"):
        del app.state.arq_pool

app = FastAPI(title="Auth Service", version="1.0", lifespan=lifespan)
app.add_middleware(
    TrustedHostMiddleware, allowed_hosts=["*"] # Заменить на домен
)
Instrumentator().instrument(app).expose(app)
app.middleware("http")(error_middleware)
app.include_router(auth_router)
