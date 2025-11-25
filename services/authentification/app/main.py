from fastapi import FastAPI, Request
from prometheus_fastapi_instrumentator import Instrumentator
from contextlib import asynccontextmanager
from redis.asyncio import Redis
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import geoip2.database
from fastapi_limiter import FastAPILimiter
from fastapi.middleware.cors import CORSMiddleware
from arq import create_pool
from arq.connections import RedisSettings
from starlette.responses import JSONResponse

from app.routers import auth
from app import (
    middleware, 
    dependencies,
    settings,
    exceptions,
    logging_config
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logging_config.setup_logging()

    try:
        geoip_reader = geoip2.database.Reader(settings.settings.app.geoip_db_path)
        app.state.geoip_reader = geoip_reader
        middleware.logger.info(f"GeoIP DB uploaded from {settings.settings.app.geoip_db_path}")
    except FileNotFoundError:
        middleware.logger.error(
            f"GeoIP DB not found on the way: {settings.settings.app.geoip_db_path}. "
            "Geolocation service will not work."
        )
        app.state.geoip_reader = None
    except Exception as e:
        middleware.logger.error(f"Error when uploading GeoIP DB: {e}")
        app.state.geoip_reader = None

    redis_pool = await dependencies.create_redis_pool()
    app.state.redis_pool = redis_pool
    redis_limiter = Redis(connection_pool=redis_pool)
    await FastAPILimiter.init(redis_limiter)
    arq_redis_settings = RedisSettings.from_dsn(settings.settings.app.redis_url)
    arq_pool = await create_pool(
        arq_redis_settings, 
        default_queue_name=settings.settings.app.arq_queue_name
    )
    app.state.arq_pool = arq_pool

    yield
    
    if app.state.geoip_reader is not None:
        app.state.geoip_reader.close()
        middleware.logger.info("GeoIP DB Reader is closed.")
        del app.state.geoip_reader
    await FastAPILimiter.close()
    await dependencies.close_redis_pool(redis_pool)
    if arq_pool:
        await arq_pool.close()
    del app.state.redis_pool
    del app.state.arq_pool

app = FastAPI(title="Auth Service", version="1.0", lifespan=lifespan)

@app.exception_handler(exceptions.AuthServiceError)
async def auth_service_exception_handler(request: Request, exc: exceptions.AuthServiceError):
    status_code = 400
    detail = str(exc)
    
    if isinstance(exc, (exceptions.InvalidCredentialsError, exceptions.InvalidTokenError, exceptions.UserInactiveError)):
        status_code = 401
    elif isinstance(exc, exceptions.UserNotFoundError):
        status_code = 404
    elif isinstance(exc, exceptions.EmailAlreadyExistsError):
        status_code = 409
    elif isinstance(exc, exceptions.TooManyAttemptsError):
        status_code = 429

    return JSONResponse(
        status_code=status_code,
        content={"status": "error", "action": "unknown", "detail": detail},
    )

app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=[
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
        "192.168.65.1",
        "*.local",
    ],
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.settings.app.frontend_url],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
Instrumentator().instrument(app).expose(app)
app.middleware("http")(middleware.error_middleware)
app.include_router(auth.router)
