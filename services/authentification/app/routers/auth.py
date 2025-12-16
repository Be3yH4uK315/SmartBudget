from uuid import UUID
from fastapi import APIRouter, Depends, Header, Query, Body, HTTPException, Request, Response
from fastapi_limiter.depends import RateLimiter
import base64
from functools import lru_cache
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

from app import (
    dependencies,
    exceptions,
    middleware,
    models,
    schemas,
    settings,
    services
)

router = APIRouter(tags=["auth"])

def _set_auth_cookies(
    response: Response,
    access_token: str,
    refresh_token: str
):
    """Хелпер для установки httpOnly cookie."""
    secure = (settings.settings.app.env == 'prod')
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=secure,
        samesite='None',
        path='/',
        max_age=900,  # 15 min
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=secure,
        samesite='None',
        path='/',
        max_age=2592000,  # 30 days
    )

def _delete_auth_cookies(response: Response):
    """Хелпер для удаления auth cookie."""
    secure = (settings.settings.app.env == 'prod')
    response.delete_cookie("access_token", httponly=True, secure=secure, samesite='None', path='/')
    response.delete_cookie("refresh_token", httponly=True, secure=secure, samesite='None', path='/')


@router.post(
    "/verify-email",
    status_code=200,
    dependencies=[Depends(RateLimiter(times=5, seconds=60))],
    response_model=schemas.UnifiedResponse
)
async def verify_email(
    body: schemas.VerifyEmailRequest = Body(...),
    service: services.AuthService = Depends(services.AuthService)
):
    """Инициирует процесс проверки электронной почты."""
    action = await service.start_email_verification(body.email)
    detail = "Complete sign in." if action == "sign_in" else "Verification email sent."
    return schemas.UnifiedResponse(
        status="success", 
        action=action, 
        detail=detail
    )

@router.get("/verify-link", status_code=200, response_model=schemas.UnifiedResponse)
async def verify_link(
    token: str = Query(...),
    email: str = Query(...),
    token_type: str = Query(...),
    service: services.AuthService = Depends(services.AuthService),
):
    """Проверяет токен подтверждения по ссылке электронной почты."""
    if token_type == 'verification':
        await service.validate_email_verification_token(token, email)
    elif token_type == 'reset':
        await service.validate_password_reset_token(token, email)
    else:
        raise HTTPException(status_code=400, detail="Invalid token type")

    return schemas.UnifiedResponse(
        status="success",
        action="verify_link",
        detail="Token validated.",
    )

@router.post(
    "/complete-registration", 
    status_code=200, 
    dependencies=[Depends(RateLimiter(times=5, seconds=60))],
    response_model=schemas.UnifiedResponse
)
async def complete_registration(
    response: Response,
    body: schemas.CompleteRegistrationRequest = Body(...),
    service: services.AuthService = Depends(services.AuthService),
    ip: str = Depends(dependencies.get_real_ip),
    user_agent: str | None = Header(None, alias="User-Agent")
):
    """Завершает регистрацию пользователя после верификации."""
    _user, _session, access_token, refresh_token = await service.complete_registration(
        body, 
        ip, 
        user_agent or "Unknown"
    )

    _set_auth_cookies(response, access_token, refresh_token)
    
    return schemas.UnifiedResponse(
        status="success", 
        action="complete_registration", 
        detail="Registration completed."
    )

@router.post(
    "/login", 
    status_code=200, 
    dependencies=[Depends(RateLimiter(times=5, seconds=60))],
    response_model=schemas.UnifiedResponse
)
async def login(
    response: Response,
    body: schemas.LoginRequest = Body(...),
    service: services.AuthService = Depends(services.AuthService),
    ip: str = Depends(dependencies.get_real_ip),
    user_agent: str | None = Header(None, alias="User-Agent")
):
    """Обрабатывает вход пользователя в систему и создает сеанс."""
    _user, _session, access_token, refresh_token = await service.authenticate_user(
        body, 
        ip, 
        user_agent or "Unknown"
    )

    _set_auth_cookies(response, access_token, refresh_token)

    return schemas.UnifiedResponse(
        status="success", 
        action="login", 
        detail="Login successful."
    )

@router.post(
    "/logout", 
    status_code=200,
    response_model=schemas.UnifiedResponse
)
async def logout(
    response: Response,
    request: Request,
    service: services.AuthService = Depends(services.AuthService),
    user_id: str | None = Depends(dependencies.get_user_id_from_expired_token)
):
    """Обрабатывает выход пользователя из системы и отменяет сеанс."""
    refresh_token = request.cookies.get("refresh_token")
    if user_id and refresh_token:
        try:
            await service.logout(user_id, refresh_token)
        except exceptions.AuthServiceError as e:
            middleware.logger.warning(f"Failed to revoke session during logout: {e}")

    _delete_auth_cookies(response)

    return schemas.UnifiedResponse(
        status="success", 
        action="logout", 
        detail="Logout successful."
    )

@router.post(
    "/reset-password", 
    status_code=200, 
    dependencies=[Depends(RateLimiter(times=5, seconds=60))],
    response_model=schemas.UnifiedResponse
)
async def reset_password(
    body: schemas.ResetPasswordRequest = Body(...),
    service: services.AuthService = Depends(services.AuthService)
):
    """Инициирует процесс сброса пароля."""
    await service.start_password_reset(body.email)

    return schemas.UnifiedResponse(
        status="success", 
        action="reset_password", 
        detail="Reset email sent."
    )

@router.post(
    "/complete-reset", 
    status_code=200,
    response_model=schemas.UnifiedResponse
)
async def complete_reset(
    body: schemas.CompleteResetRequest = Body(...),
    service: services.AuthService = Depends(services.AuthService)
):
    """Завершает сброс пароля с помощью нового пароля."""
    await service.complete_password_reset(body)

    return schemas.UnifiedResponse(
        status="success", 
        action="complete_reset", 
        detail="Password reset completed."
    )

@router.post(
    "/change-password", 
    status_code=200,
    response_model=schemas.UnifiedResponse
)
async def change_password(
    body: schemas.ChangePasswordRequest = Body(...),
    service: services.AuthService = Depends(services.AuthService),
    user: models.User = Depends(dependencies.get_current_active_user)
):
    """Изменяет пароль пользователя после проверки подлинности."""
    await service.change_password(user.id, body)

    return schemas.UnifiedResponse(
        status="success", 
        action="change_password", 
        detail="Password changed."
    )

@router.get("/me", status_code=200, response_model=schemas.UserInfo)
async def get_current_user_info(
    user: models.User = Depends(dependencies.get_current_active_user)
):
    """Возвращает информацию о текущем аутентифицированном пользователе."""
    return user

@router.get(
    "/sessions",
    status_code=200,
    response_model=schemas.AllSessionsResponse
)
async def get_all_user_sessions(
    request: Request,
    service: services.AuthService = Depends(services.AuthService),
    user: models.User = Depends(dependencies.get_current_active_user)
):
    """Получает список всех активных сессий для текущего пользователя."""
    current_refresh_token = request.cookies.get("refresh_token")
    sessions_list = await service.get_all_sessions(user.id, current_refresh_token)
    return schemas.AllSessionsResponse(sessions=sessions_list)


@router.delete(
    "/sessions/{session_id}", 
    status_code=200,
    response_model=schemas.UnifiedResponse
)
async def revoke_session(
    session_id: UUID,
    service: services.AuthService = Depends(services.AuthService),
    user: models.User = Depends(dependencies.get_current_active_user)
):
    """Отзывает одну конкретную сессию по ее ID."""
    await service.revoke_session_by_id(user.id, session_id)

    return schemas.UnifiedResponse(
        status="success",
        action="revoke_session",
        detail="Session has been revoked."
    )


@router.post(
    "/sessions/logout-others", 
    status_code=200,
    dependencies=[Depends(RateLimiter(times=5, seconds=60))],
    response_model=schemas.UnifiedResponse
)
async def revoke_other_sessions(
    request: Request,
    service: services.AuthService = Depends(services.AuthService),
    user: models.User = Depends(dependencies.get_current_active_user)
):
    """Отзывает все сессии, кроме текущей."""
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    await service.revoke_other_sessions(user.id, refresh_token)

    return schemas.UnifiedResponse(
        status="success",
        action="revoke_other_sessions",
        detail="All other sessions have been revoked."
    )

@router.post(
    "/validate-token", 
    status_code=200,
    response_model=schemas.UnifiedResponse
)
async def validate_token(
    body: schemas.TokenValidateRequest = Body(...),
    service: services.AuthService = Depends(services.AuthService)
):
    """Проверяет access_token."""
    await service.validate_access_token_async(body.token)

    return schemas.UnifiedResponse(
        status="success", 
        action="validate_token", 
        detail="Token valid."
    )

@router.post(
    "/refresh", 
    status_code=200, 
    dependencies=[Depends(RateLimiter(times=30, seconds=60))],
    response_model=schemas.UnifiedResponse
)
async def refresh(
    response: Response,
    request: Request,
    service: services.AuthService = Depends(services.AuthService)
):
    """Обновляет access_token с помощью refresh_token"""
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Missing refresh token")
    new_access_token, new_refresh_token = await service.refresh_session(refresh_token)

    _set_auth_cookies(response, new_access_token, new_refresh_token)

    return schemas.UnifiedResponse(
        status="success",
        action="refresh",
        detail="Tokens refreshed.",
    )

def _int_to_base64url(value: int) -> str:
    """Преобразует целое число в строку base64url."""
    byte_len = (value.bit_length() + 7) // 8
    if byte_len == 0:
        byte_len = 1
    bytes_val = value.to_bytes(byte_len, "big", signed=False)
    return base64.urlsafe_b64encode(bytes_val).decode("utf-8").rstrip("=")

@lru_cache(maxsize=1)
@router.get("/.well-known/jwks.json")
async def get_jwks():
    """Предоставляет JWKS для проверки токенов."""
    public_key_obj = serialization.load_pem_public_key(
        settings.settings.jwt.jwt_public_key.encode(),
        backend=default_backend()
    )
    public_numbers = public_key_obj.public_numbers()

    jwks = {
        "keys": [
            {
                "kty": "RSA",
                "use": "sig",
                "kid": "sig-1",
                "alg": "RS256",
                "n": _int_to_base64url(public_numbers.n),
                "e": _int_to_base64url(public_numbers.e),
            }
        ]
    }
    return jwks