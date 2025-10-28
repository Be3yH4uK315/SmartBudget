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

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    
    redis_pool = await create_redis_pool()
    app.state.redis_pool = redis_pool
    redis_limiter = Redis(connection_pool=redis_pool)
    await FastAPILimiter.init(redis_limiter)
    
    arq_pool = await create_pool(
        RedisSettings.from_url(settings.redis_url)
    )
    app.state.arq_pool = arq_pool

    yield
    
    await FastAPILimiter.close()
    await close_redis_pool(redis_pool)
    if arq_pool:
        await arq_pool.close()


app = FastAPI(title="Auth Service", version="1.0", lifespan=lifespan)
Instrumentator().instrument(app).expose(app)
app.middleware("http")(error_middleware)
app.include_router(auth_router)
