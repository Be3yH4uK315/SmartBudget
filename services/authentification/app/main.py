from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from app.middleware import error_middleware, setup_logging
from app.routers.auth import router as auth_router
from app.kafka import startup_kafka, shutdown_kafka
from app.tasks import app as celery_app  # Для worker
from app.settings import settings
from app.dependencies import get_redis
from fastapi_limiter import FastAPILimiter
from redis.asyncio import Redis

app = FastAPI(title="Auth Service", version="1.0")

# Middleware
app.add_middleware(error_middleware)

# Routers
app.include_router(auth_router)

# Lifecycle
@app.on_event("startup")
async def startup():
    setup_logging()
    await startup_kafka()
    redis: Redis = await get_redis().__anext__()  # Init limiter
    await FastAPILimiter.init(redis)
    Instrumentator().instrument(app).expose(app)  # Prometheus

@app.on_event("shutdown")
async def shutdown():
    await shutdown_kafka()
    await FastAPILimiter.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)