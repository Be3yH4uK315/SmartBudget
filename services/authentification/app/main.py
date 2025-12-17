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
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncEngine

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
    logging_config.setupLogging()

    try:
        geoIpReader = geoip2.database.Reader(settings.settings.APP.GEOIP_DB_PATH)
        app.state.geoIpReader = geoIpReader
        middleware.logger.info(
            f"GeoIP DB loaded: {settings.settings.APP.GEOIP_DB_PATH}"
        )
    except FileNotFoundError:
        middleware.logger.warning(
            f"GeoIP DB not found: {settings.settings.APP.GEOIP_DB_PATH}. "
            f"Geolocation service disabled."
        )
        app.state.geoIpReader = None
    except Exception as e:
        middleware.logger.error(f"GeoIP init error: {e}")
        app.state.geoIpReader = None

    try:
        engine: AsyncEngine = create_async_engine(settings.settings.DB.DB_URL)
        dbSessionMaker = async_sessionmaker(engine, expire_on_commit=False)
        app.state.engine = engine
        app.state.dbSessionMaker = dbSessionMaker
        middleware.logger.info("DB Engine & Session Maker initialized")

    except Exception as e:
        middleware.logger.critical(f"DB initialization failed: {e}")
        raise RuntimeError("Database initialization failed") from e

    try:
        redisPool = await dependencies.createRedisPool()
        app.state.redisPool = redisPool

        redisLimiter = Redis(connection_pool=redisPool)
        await FastAPILimiter.init(redisLimiter)

        middleware.logger.info("Redis pool & rate limiter initialized")
    except Exception as e:
        middleware.logger.critical(f"Redis initialization failed: {e}")
        raise RuntimeError("Redis initialization failed") from e
    
    try:
        arqSettings = RedisSettings.from_dsn(settings.settings.ARQ.REDIS_URL)
        arqPool = await create_pool(
            arqSettings,
            default_queue_name=settings.settings.ARQ.ARQ_QUEUE_NAME
        )
        app.state.arqPool = arqPool
        middleware.logger.info("ARQ Pool initialized")
    except Exception as e:
        middleware.logger.critical(f"ARQ initialization failed: {e}")
        raise RuntimeError("ARQ initialization failed") from e

    try:
        yield

    finally:
        try:
            geo = app.state.geoIpReader
            if geo is not None:
                geo.close()
                middleware.logger.info("GeoIP DB closed")
        except Exception as e:
            middleware.logger.error(f"Error closing GeoIP: {e}")

        try:
            if app.state.engine:
                await app.state.engine.dispose()
                middleware.logger.info("DB engine disposed")
        except Exception as e:
            middleware.logger.error(f"Error disposing DB engine: {e}")

        try:
            await FastAPILimiter.close()
        except Exception as e:
            middleware.logger.error(f"Error closing FastAPILimiter: {e}")

        try:
            redisPool = app.state.redisPool
            await dependencies.closeRedisPool(redisPool)
            middleware.logger.info("Redis pool closed")
        except Exception as e:
            middleware.logger.error(f"Error closing redis pool: {e}")

        try:
            if app.state.arqPool:
                await app.state.arqPool.close()
                middleware.logger.info("ARQ pool closed")
        except Exception as e:
            middleware.logger.error(f"Error closing ARQ pool: {e}")
        del app.state.redisPool
        del app.state.arqPool

app = FastAPI(
    title="Auth Service", 
    version="1.0", 
    lifespan=lifespan,
    docs_url="/api/v1/auth/docs",
    openapi_url="/api/v1/auth/openapi.json"
)

@app.exception_handler(exceptions.AuthServiceError)
async def authServiceExceptionHandler(request: Request, exc: exceptions.AuthServiceError):
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

    action = "unknown"
    try:
        action = request.url.path.strip("/").split("/")[-1]
    except Exception:
        pass

    return JSONResponse(
        status_code=status_code,
        content={"status": "error", "action": action, "detail": detail},
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
    allow_origins=[settings.settings.APP.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
Instrumentator().instrument(app).expose(app)
app.middleware("http")(middleware.errorMiddleware)
app.include_router(auth.router, prefix="/api/v1/auth")
