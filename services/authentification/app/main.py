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

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    
    redis_pool = await create_redis_pool()
    app.state.redis_pool = redis_pool
    redis_limiter = Redis(connection_pool=redis_pool)
    await FastAPILimiter.init(redis_limiter)
    arq_redis_settings = RedisSettings.from_dsn(settings.redis_url)
    arq_redis_settings.queue_name = settings.arq_queue_name
    arq_pool = await create_pool(arq_redis_settings)
    app.state.arq_pool = arq_pool

    yield
    
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
    TrustedHostMiddleware, allowed_hosts=["*"]
)
Instrumentator().instrument(app).expose(app)
app.middleware("http")(error_middleware)
app.include_router(auth_router)
