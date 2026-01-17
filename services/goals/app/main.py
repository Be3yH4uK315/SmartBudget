import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app
from arq import create_pool
from arq.connections import RedisSettings
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.database import get_db_engine, get_session_factory
from app.core.context import set_request_id
from app.core import exceptions
from app.api.routes import router as goals_router

setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление ресурсами приложения."""
    logger.info("Application startup initiated")

    engine = get_db_engine()
    app.state.engine = engine
    app.state.db_session_maker = get_session_factory(engine)

    app.state.arq_pool = await create_pool(
        RedisSettings.from_dsn(settings.ARQ.REDIS_URL),
        default_queue_name=settings.ARQ.ARQ_QUEUE_NAME,
    )
    yield
    logger.info("Application shutdown initiated")

    await app.state.arq_pool.close()
    await engine.dispose()

    logger.info("Application shutdown complete")

app = FastAPI(
    title="Goals Service",
    version="1.0",
    lifespan=lifespan,
    docs_url="/api/v1/goals/docs",
    openapi_url="/api/v1/goals/openapi.json",
)

@app.middleware("http")
async def tracing_middleware(
    request: Request,
    call_next,
):
    req_id = (
        request.headers.get("X-Request-ID")
        or request.headers.get("X-Correlation-ID")
    )
    final_id = set_request_id(req_id)
    response: Response = await call_next(request)
    response.headers["X-Request-ID"] = final_id

    return response

metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

@app.exception_handler(exceptions.GoalServiceError)
async def goal_service_exception_handler(
    request: Request,
    exc: exceptions.GoalServiceError,
):
    """Обработка ошибок бизнес-логики."""
    status_code = 400
    if isinstance(exc, exceptions.GoalNotFoundError):
        status_code = 404

    logger.warning(
        "Service error: %s: %s",
        type(exc).__name__,
        exc,
    )

    return JSONResponse(
        status_code=status_code,
        content={"detail": str(exc)},
    )

@app.exception_handler(SQLAlchemyError)
async def db_error_handler(
    request: Request,
    exc: SQLAlchemyError,
):
    """Обработка ошибок БД."""
    logger.error(
        "Database error: %s",
        exc,
        exc_info=True,
    )

    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )

@app.exception_handler(Exception)
async def general_exception_handler(
    request: Request,
    exc: Exception,
):
    """Обработка неожиданных ошибок."""
    logger.critical(
        "Unhandled exception: %s",
        exc,
        exc_info=True,
    )

    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )

app.include_router(
    goals_router,
    prefix="/api/v1/goals",
)