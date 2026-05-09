from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from prometheus_client import make_asgi_app
from smartbudget_shared.request_logging import setup_request_logging

from app.api.exception_handlers import setup_exception_handlers
from app.api.v1 import api_router
from app.core.context import set_request_id
from app.core.logging import setup_logging
from app.lifespan import lifespan

setup_logging()

app = FastAPI(
    title="Transactions Service",
    version="1.0",
    lifespan=lifespan,
    default_response_class=ORJSONResponse,
    docs_url="/api/v1/transactions/docs",
    openapi_url="/api/v1/transactions/openapi.json",
)

setup_request_logging(app, set_request_id)
setup_exception_handlers(app)

metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

app.include_router(api_router, prefix="/api/v1")
