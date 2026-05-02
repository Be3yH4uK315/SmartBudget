import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.responses import ORJSONResponse
from prometheus_client import make_asgi_app
from sqlalchemy.exc import SQLAlchemyError

from app.api.routes import router as transactions_router
from app.core import exceptions
from app.core.context import set_request_id
from app.core.database import get_db_engine, get_session_factory
from app.core.logging import setup_logging
from app.infrastructure.kafka.producer import KafkaProducerWrapper

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup initiated")

    engine = get_db_engine()
    app.state.engine = engine
    app.state.db_session_maker = get_session_factory(engine)
    app.state.kafka_producer = None

    producer = KafkaProducerWrapper()
    try:
        await producer.start()
        app.state.kafka_producer = producer
    except Exception as exc:
        logger.error("Kafka producer startup failed: %s", exc, exc_info=True)

    yield

    logger.info("Application shutdown initiated")

    if app.state.kafka_producer:
        await app.state.kafka_producer.stop()

    await engine.dispose()
    logger.info("Application shutdown complete")


app = FastAPI(
    title="Transactions Service",
    version="1.0",
    lifespan=lifespan,
    default_response_class=ORJSONResponse,
    docs_url="/api/v1/transactions/docs",
    openapi_url="/api/v1/transactions/openapi.json",
)


@app.middleware("http")
async def tracing_middleware(request: Request, call_next):
    req_id = request.headers.get("X-Request-ID") or request.headers.get("X-Correlation-ID")
    final_id = set_request_id(req_id)
    response: Response = await call_next(request)
    response.headers["X-Request-ID"] = final_id
    return response


metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.exception_handler(exceptions.TransactionServiceError)
async def service_exception_handler(request: Request, exc: exceptions.TransactionServiceError):
    status_code = 400
    if isinstance(exc, exceptions.TransactionNotFoundError):
        status_code = 404
    elif isinstance(exc, exceptions.TransactionAccessDeniedError):
        status_code = 403

    logger.warning("Service error: %s: %s", type(exc).__name__, exc)
    return ORJSONResponse(status_code=status_code, content={"detail": str(exc)})


@app.exception_handler(SQLAlchemyError)
async def db_error_handler(request: Request, exc: SQLAlchemyError):
    logger.error("Database error: %s", exc, exc_info=True)
    return ORJSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.critical("Unhandled exception: %s", exc, exc_info=True)
    return ORJSONResponse(status_code=500, content={"detail": "Internal server error"})


app.include_router(transactions_router, prefix="/api/v1/transactions")
