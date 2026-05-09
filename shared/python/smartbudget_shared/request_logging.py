import logging
import time
from collections.abc import Awaitable, Callable
from uuid import uuid4

from fastapi import FastAPI, Request, Response

logger = logging.getLogger("smartbudget.request")

RequestIdSetter = Callable[[str | None], str]
CallNext = Callable[[Request], Awaitable[Response]]


def setup_request_logging(
    app: FastAPI,
    set_request_id: RequestIdSetter | None = None,
) -> None:
    """Регистрирует middleware логирования HTTP-запросов."""

    @app.middleware("http")
    async def request_logging_middleware(
        request: Request,
        call_next: CallNext,
    ) -> Response:
        incoming_id = request.headers.get("X-Request-ID") or request.headers.get(
            "X-Correlation-ID",
        )
        request_id = (
            set_request_id(incoming_id)
            if set_request_id
            else incoming_id or str(uuid4())
        )

        started_at = time.perf_counter()
        status_code = 500
        response: Response | None = None

        try:
            response = await call_next(request)
            status_code = response.status_code
            return response

        except Exception:
            logger.exception(
                "request failed method=%s path=%s request_id=%s",
                request.method,
                request.url.path,
                request_id,
                extra={
                    "extra": {
                        "method": request.method,
                        "path": request.url.path,
                        "request_id": request_id,
                    },
                },
            )
            raise

        finally:
            duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
            client = request.client.host if request.client else None

            logger.info(
                (
                    "request completed method=%s path=%s status_code=%s "
                    "duration_ms=%.2f request_id=%s client=%s"
                ),
                request.method,
                request.url.path,
                status_code,
                duration_ms,
                request_id,
                client,
                extra={
                    "extra": {
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": status_code,
                        "duration_ms": duration_ms,
                        "request_id": request_id,
                        "client": client,
                    },
                },
            )

            if response is not None:
                response.headers["X-Request-ID"] = request_id
