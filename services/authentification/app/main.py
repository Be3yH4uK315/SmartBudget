from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from contextlib import asynccontextmanager
from redis import Redis
from app.middleware import error_middleware, setup_logging
from app.routers.auth import router as auth_router
from app.kafka import startup_kafka, shutdown_kafka
from app.dependencies import create_redis_pool, close_redis_pool, get_redis
from fastapi_limiter import FastAPILimiter

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    await startup_kafka()
    redis_pool = await create_redis_pool()
    app.state.redis_pool = redis_pool
    redis_client = Redis(connection_pool=redis_pool, decode_responses=True)
    await FastAPILimiter.init(redis_client)
    yield
    await shutdown_kafka()
    await close_redis_pool(redis_pool)
    await FastAPILimiter.close()

app = FastAPI(title="Auth Service", version="1.0", lifespan=lifespan)
Instrumentator().instrument(app).expose(app)
app.middleware("http")(error_middleware)
app.include_router(auth_router)