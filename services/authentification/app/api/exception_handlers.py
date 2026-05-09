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
        exceptions.AuthServiceError,
        auth_service_exception_handler,
    )
    app.add_exception_handler(SQLAlchemyError, db_error_handler)
    app.add_exception_handler(Exception, general_exception_handler)


async def auth_service_exception_handler(
    request: Request,
    exc: exceptions.AuthServiceError,
) -> ORJSONResponse:
    """Обрабатывает бизнес-ошибки сервиса авторизации."""
    status_code = _get_auth_error_status_code(exc)
    detail = str(exc)
    action = _get_action_from_request(request)

    logger.warning(
        "Service error: %s: %s",
        type(exc).__name__,
        detail,
        extra={
            "path": request.url.path,
            "method": request.method,
            "action": action,
            "status_code": status_code,
        },
    )

    return ORJSONResponse(
        status_code=status_code,
        content={
            "status": "error",
            "action": action,
            "detail": detail,
        },
    )


async def db_error_handler(request: Request, exc: SQLAlchemyError) -> ORJSONResponse:
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


async def general_exception_handler(request: Request, exc: Exception) -> ORJSONResponse:
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


def _get_auth_error_status_code(exc: exceptions.AuthServiceError) -> int:
    """Возвращает HTTP-код для бизнес-ошибки авторизации."""
    if isinstance(
        exc,
        (
            exceptions.InvalidCredentialsError,
            exceptions.InvalidTokenError,
            exceptions.UserInactiveError,
            exceptions.SessionExpiredError,
        ),
    ):
        return HTTPStatus.UNAUTHORIZED

    if isinstance(exc, exceptions.UserNotFoundError):
        return HTTPStatus.NOT_FOUND

    if isinstance(exc, exceptions.EmailAlreadyExistsError):
        return HTTPStatus.CONFLICT

    if isinstance(exc, exceptions.TooManyAttemptsError):
        return HTTPStatus.TOO_MANY_REQUESTS

    return HTTPStatus.BAD_REQUEST


def _get_action_from_request(request: Request) -> str:
    """Определяет действие по последнему сегменту URL."""
    return request.url.path.strip("/").split("/")[-1] or "unknown"
