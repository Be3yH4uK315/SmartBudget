import logging

from fastapi import (
    APIRouter,
    Body,
    Depends,
    Header,
    HTTPException,
    Query,
    Request,
    Response,
    status,
)
from fastapi_limiter.depends import RateLimiter

from app.api import dependencies
from app.core import exceptions
from app.domain.schemas import api as schemas
from app.services.login_service import LoginService
from app.services.password_service import PasswordService
from app.services.registration_service import RegistrationService
from app.services.session_service import SessionService
from app.utils import cookies

logger = logging.getLogger(__name__)

router = APIRouter(tags=["auth"])


@router.post(
    "/verify-email",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RateLimiter(times=5, seconds=60))],
    response_model=schemas.UnifiedResponse,
    summary="Начало верификации email",
)
async def verify_email(
    body: schemas.VerifyEmailRequest = Body(...),
    reg_service: RegistrationService = Depends(dependencies.get_registration_service),
):
    action = await reg_service.start_email_verification(body.email)
    detail = "Complete sign in." if action == "sign_in" else "Verification email sent."

    return schemas.UnifiedResponse(
        status="success",
        action=action,
        detail=detail,
    )


@router.get(
    "/verify-link",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RateLimiter(times=5, seconds=60))],
    response_model=schemas.UnifiedResponse,
    summary="Проверка верификационной или сбросной ссылки",
)
async def verify_link(
    token: str = Query(...),
    email: str = Query(...),
    token_type: str = Query(..., alias="tokenType"),
    reg_service: RegistrationService = Depends(dependencies.get_registration_service),
    pwd_service: PasswordService = Depends(dependencies.get_password_service),
):
    if token_type == "verification":
        await reg_service.validate_email_verification_token(token, email)
    elif token_type == "reset":
        await pwd_service.validate_password_reset_token(token, email)
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token type")

    return schemas.UnifiedResponse(
        status="success",
        action="verify_link",
        detail="Token validated.",
    )


@router.post(
    "/complete-registration",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RateLimiter(times=5, seconds=60))],
    response_model=schemas.UnifiedResponse,
    summary="Завершение регистрации пользователя",
)
async def complete_registration(
    response: Response,
    body: schemas.CompleteRegistrationRequest = Body(...),
    reg_service: RegistrationService = Depends(dependencies.get_registration_service),
    ip: str = Depends(dependencies.get_real_ip),
    user_agent: str | None = Header(None, alias="User-Agent"),
):
    (
        _user,
        _session,
        access_token,
        refresh_token,
    ) = await reg_service.complete_registration(
        body,
        ip,
        user_agent or "Unknown",
    )

    cookies.set_auth_cookies(response, access_token, refresh_token)

    return schemas.UnifiedResponse(
        status="success",
        action="completeRegistration",
        detail="Registration completed.",
    )


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RateLimiter(times=5, seconds=60))],
    response_model=schemas.UnifiedResponse,
    summary="Аутентификация пользователя",
)
async def login(
    response: Response,
    body: schemas.LoginRequest = Body(...),
    login_service: LoginService = Depends(dependencies.get_login_service),
    ip: str = Depends(dependencies.get_real_ip),
    user_agent: str | None = Header(None, alias="User-Agent"),
):
    (
        _user,
        _session,
        access_token,
        refresh_token,
    ) = await login_service.authenticate_user(
        body,
        ip,
        user_agent or "Unknown",
    )

    cookies.set_auth_cookies(response, access_token, refresh_token)

    return schemas.UnifiedResponse(
        status="success",
        action="login",
        detail="Login successful.",
    )


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    response_model=schemas.UnifiedResponse,
    summary="Выход пользователя из системы",
)
async def logout(
    response: Response,
    request: Request,
    login_service: LoginService = Depends(dependencies.get_login_service),
    user_id: str | None = Depends(dependencies.get_user_id_from_expired_token),
):
    refresh_token = request.cookies.get("refresh_token")

    if user_id and refresh_token:
        try:
            await login_service.logout(user_id, refresh_token)
        except exceptions.AuthServiceError as exc:
            logger.warning("Failed to revoke session during logout: %s", exc)

    cookies.delete_auth_cookies(response)

    return schemas.UnifiedResponse(
        status="success",
        action="logout",
        detail="Logout successful.",
    )


@router.post(
    "/reset-password",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RateLimiter(times=5, seconds=60))],
    response_model=schemas.UnifiedResponse,
    summary="Начало сброса пароля пользователя",
)
async def reset_password(
    body: schemas.ResetPasswordRequest = Body(...),
    pwd_service: PasswordService = Depends(dependencies.get_password_service),
):
    await pwd_service.start_password_reset(body.email)

    return schemas.UnifiedResponse(
        status="success",
        action="resetPassword",
        detail="Reset email sent.",
    )


@router.post(
    "/complete-reset",
    status_code=status.HTTP_200_OK,
    response_model=schemas.UnifiedResponse,
    summary="Завершение сброса пароля пользователя",
)
async def complete_reset(
    body: schemas.CompleteResetRequest = Body(...),
    pwd_service: PasswordService = Depends(dependencies.get_password_service),
):
    await pwd_service.complete_password_reset(body)

    return schemas.UnifiedResponse(
        status="success",
        action="completeReset",
        detail="Password reset completed.",
    )


@router.post(
    "/validate-token",
    status_code=status.HTTP_200_OK,
    response_model=schemas.UnifiedResponse,
    summary="Валидация access токена пользователя",
)
async def validate_token(
    body: schemas.TokenValidateRequest = Body(...),
    session_service: SessionService = Depends(dependencies.get_session_service),
):
    await session_service.validate_access_token(body.token)

    return schemas.UnifiedResponse(
        status="success",
        action="validateToken",
        detail="Token valid.",
    )


@router.post(
    "/refresh",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RateLimiter(times=30, seconds=60))],
    response_model=schemas.UnifiedResponse,
    summary="Обновление access и refresh токенов пользователя",
)
async def refresh(
    response: Response,
    request: Request,
    session_service: SessionService = Depends(dependencies.get_session_service),
):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token")

    new_access_token, new_refresh_token = await session_service.refresh_session(
        refresh_token,
    )

    cookies.set_auth_cookies(response, new_access_token, new_refresh_token)

    return schemas.UnifiedResponse(
        status="success",
        action="refresh",
        detail="Tokens refreshed.",
    )
