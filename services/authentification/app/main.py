from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from contextlib import asynccontextmanager
from app.middleware import error_middleware, setup_logging
from app.routers.auth import router as auth_router
from app.kafka import startup_kafka, shutdown_kafka
from app.dependencies import get_redis
from fastapi_limiter import FastAPILimiter

app = FastAPI(title="Auth Service", version="1.0")
Instrumentator().instrument(app).expose(app)
app.middleware("http")(error_middleware)
app.include_router(auth_router)

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    await startup_kafka()
    async with get_redis() as redis:
        await FastAPILimiter.init(redis)
        yield
    await shutdown_kafka()
    await FastAPILimiter.close()

app.router.lifespan_context = lifespan

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, workers=4, reload=True)