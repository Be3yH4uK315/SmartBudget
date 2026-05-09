from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from smartbudget_shared.request_logging import setup_request_logging

from app.api.exception_handlers import setup_exception_handlers
from app.api.v1 import api_router
from app.core.logging import setup_logging
from app.lifespan import lifespan

setup_logging()

app = FastAPI(
    title="Classification Service",
    version="1.0",
    lifespan=lifespan,
    default_response_class=ORJSONResponse,
    docs_url="/api/v1/class/docs",
    openapi_url="/api/v1/class/openapi.json",
)

setup_request_logging(app)
setup_exception_handlers(app)

Instrumentator().instrument(app).expose(app)

app.include_router(api_router, prefix="/api/v1/class")
