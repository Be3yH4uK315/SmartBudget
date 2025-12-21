import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from arq import create_pool
from arq.connections import RedisSettings
from redis.asyncio import Redis
import geoip2.database
from fastapi_limiter import FastAPILimiter

from app import exceptions, middleware, settings, dependencies, logging_config
from app.routers import auth

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление ресурсами приложения."""
    logging_config.setup_logging()
    logger.info("Application startup initiated")

    engine = None
    db_session_maker = None
    arq_pool = None
    redis_pool = None
    geoip_reader = None

    try:
        try:
            engine = create_async_engine(
                settings.settings.DB.DB_URL,
                pool_size=settings.settings.DB.DB_POOL_SIZE,
                max_overflow=settings.settings.DB.DB_MAX_OVERFLOW,
                echo=False
            )
            db_session_maker = async_sessionmaker(
                engine, 
                class_=AsyncSession, 
                expire_on_commit=False
            )
            app.state.engine = engine
            app.state.db_session_maker = db_session_maker
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

        try:
            geoip_reader = geoip2.database.Reader(
                settings.settings.APP.GEOIP_DB_PATH
            )
            app.state.geoip_reader = geoip_reader
            logger.info("GeoIP initialized")
        except FileNotFoundError:
            app.state.geoip_reader = None
            logger.warning("GeoIP DB not found, service disabled")
        except Exception as e:
            app.state.geoip_reader = None
            logger.error(f"GeoIP init error: {e}")

        try:
            redis_pool = await dependencies.create_redis_pool()
            app.state.redis_pool = redis_pool

            redis = Redis(connection_pool=redis_pool)
            await FastAPILimiter.init(redis)

            logger.info("Redis pool & rate limiter initialized")
        except Exception as e:
            app.state.redis_pool = None
            logger.error(f"Redis init failed, limiter disabled: {e}")

        try:
            arq_settings = RedisSettings.from_dsn(
                settings.settings.ARQ.REDIS_URL
            )
            arq_pool = await create_pool(
                arq_settings,
                default_queue_name=settings.settings.ARQ.ARQ_QUEUE_NAME,
            )
            app.state.arq_pool = arq_pool
            logger.info("ARQ Redis pool initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ARQ: {e}")

        logger.info("Application startup complete")
        yield

    finally:
        logger.info("Application shutdown initiated")

        if geoip_reader:
            try:
                geoip_reader.close()
                logger.info("GeoIP closed")
            except Exception as e:
                logger.error(f"GeoIP close error: {e}")

        if redis_pool:
            try:
                await FastAPILimiter.close()
                await dependencies.close_redis_pool(redis_pool)
                logger.info("Redis pool closed")
            except Exception as e:
                logger.error(f"Redis close error: {e}")

        if arq_pool:
            try:
                await arq_pool.close()
                logger.info("ARQ pool closed")
            except Exception as e:
                logger.error(f"Error closing ARQ pool: {e}")

        if engine:
            try:
                await engine.dispose()
                logger.info("Database disposed")
            except Exception as e:
                logger.error(f"Error disposing database: {e}")
        
        logger.info("Application shutdown complete")

app = FastAPI(
    title="Auth Service", 
    version="1.0", 
    lifespan=lifespan,
    docs_url="/api/v1/auth/docs",
    openapi_url="/api/v1/auth/openapi.json"
)

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

    action = "unknown"
    try:
        action = request.url.path.strip("/").split("/")[-1]
    except Exception:
        pass

    return JSONResponse(
        status_code=status_code,
        content={"status": "error", "action": action, "detail": detail},
    )

Instrumentator().instrument(app).expose(app)
app.middleware("http")(middleware.error_middleware)
app.include_router(auth.router, prefix="/api/v1/auth")
