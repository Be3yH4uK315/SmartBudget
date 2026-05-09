import logging
from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.responses import ORJSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.core import exceptions

logger = logging.getLogger(__name__)


def setup_exception_handlers(app: FastAPI) -> None:
    """Регистрирует обработчики исключений приложения."""
    app.add_exception_handler(
        exceptions.TransactionServiceError,
        transaction_service_exception_handler,
    )
    app.add_exception_handler(SQLAlchemyError, db_error_handler)
    app.add_exception_handler(Exception, general_exception_handler)


async def transaction_service_exception_handler(
    request: Request,
    exc: exceptions.TransactionServiceError,
) -> ORJSONResponse:
    """Обрабатывает бизнес-ошибки сервиса транзакций."""
    status_code = _get_transaction_error_status_code(exc)

    logger.warning(
        "Service error: %s: %s",
        type(exc).__name__,
        exc,
        extra={
            "path": request.url.path,
            "method": request.method,
            "status_code": status_code,
        },
    )

    return ORJSONResponse(
        status_code=status_code,
        content={"detail": str(exc)},
    )


async def db_error_handler(
    request: Request,
    exc: SQLAlchemyError,
) -> ORJSONResponse:
    """Обрабатывает ошибки базы данных."""
    logger.error(
        "Database error: %s",
        exc,
        extra={
            "path": request.url.path,
            "method": request.method,
        },
        exc_info=True,
    )

    return ORJSONResponse(
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


async def general_exception_handler(
    request: Request,
    exc: Exception,
) -> ORJSONResponse:
    """Обрабатывает неожиданные ошибки приложения."""
    logger.critical(
        "Unhandled exception: %s",
        exc,
        extra={
            "path": request.url.path,
            "method": request.method,
            "error_type": type(exc).__name__,
        },
        exc_info=True,
    )

    return ORJSONResponse(
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


def _get_transaction_error_status_code(
    exc: exceptions.TransactionServiceError,
) -> int:
    """Возвращает HTTP-код для бизнес-ошибки сервиса транзакций."""
    if isinstance(exc, exceptions.TransactionNotFoundError):
        return HTTPStatus.NOT_FOUND

    if isinstance(exc, exceptions.TransactionAccessDeniedError):
        return HTTPStatus.FORBIDDEN

    return HTTPStatus.BAD_REQUEST
