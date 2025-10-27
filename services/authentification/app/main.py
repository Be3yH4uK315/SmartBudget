from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from contextlib import asynccontextmanager
from app.middleware import error_middleware, setup_logging
from app.routers.auth import router as auth_router
from app.kafka import startup_kafka, shutdown_kafka
from app.dependencies import get_redis
from fastapi_limiter import FastAPILimiter

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    await startup_kafka()
    # НАДО исправить
    redis_client = get_redis()
    await FastAPILimiter.init(redis_client)
    yield
    await shutdown_kafka()
    await redis_client.close()
    await FastAPILimiter.close()

app = FastAPI(title="Auth Service", version="1.0", lifespan=lifespan)
Instrumentator().instrument(app).expose(app)
app.middleware("http")(error_middleware)
app.include_router(auth_router)