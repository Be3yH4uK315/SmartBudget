from fastapi import APIRouter, Depends, Query, Body, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from fastapi_limiter.depends import RateLimiter
import base64
from functools import lru_cache

from app.dependencies import get_current_user_id, get_real_ip
from app.schemas import (
    UnifiedResponse, VerifyEmailRequest, CompleteRegistrationRequest,
    LoginRequest, ResetPasswordRequest, CompleteResetRequest,
    ChangePasswordRequest, TokenValidateRequest
)
from app.settings import settings
from app.services import AuthService

router = APIRouter(prefix="/api/auth", tags=["auth"])

def _set_auth_cookies(
    response: Response,
    access_token: str,
    refresh_token: str
):
    """Хелпер для установки httpOnly cookie."""
    secure = (settings.env == 'prod')
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
    secure = (settings.env == 'prod')
    response.delete_cookie("access_token", httponly=True, secure=secure, samesite='None', path='/')
    response.delete_cookie("refresh_token", httponly=True, secure=secure, samesite='None', path='/')


@router.post(
    "/verify-email",
    status_code=200,
    dependencies=[Depends(RateLimiter(times=5, seconds=60))],
)
async def verify_email(
    body: VerifyEmailRequest = Body(...),
    service: AuthService = Depends(AuthService)
):
    """Инициирует процесс проверки электронной почты."""
    action = await service.start_email_verification(body.email)
    detail = "Complete sign in." if action == "sign_in" else "Verification email sent."
    return JSONResponse(
        UnifiedResponse(
            status="success", 
            action=action, 
            detail=detail
        ).model_dump()
    )

@router.get("/verify-link", status_code=200)
async def verify_link(
    token: str = Query(...),
    email: str = Query(...),
    token_type: str = Query(...),
    service: AuthService = Depends(AuthService)
):
    """Проверяет токен подтверждения по ссылке электронной почты."""
    await service.validate_verification_token(token, email, token_type)
    return JSONResponse(
        UnifiedResponse(
            status="success",
            action="verify_link",
            detail="Token validated.",
        ).model_dump()
    )

@router.post(
    "/complete-registration", 
    status_code=200, 
    dependencies=[Depends(RateLimiter(times=5, seconds=60))]
)
async def complete_registration(
    body: CompleteRegistrationRequest = Body(...),
    service: AuthService = Depends(AuthService),
    ip: str = Depends(get_real_ip)
):
    """Завершает регистрацию пользователя после верификации."""
    _user, _session, access_token, refresh_token = await service.complete_registration(body, ip)

    response = JSONResponse(
        UnifiedResponse(
            status="success", 
            action="complete_registration", 
            detail="Registration completed."
        ).model_dump()
    )
    _set_auth_cookies(response, access_token, refresh_token)
    return response

@router.post("/login", status_code=200, dependencies=[Depends(RateLimiter(times=5, seconds=60))])
async def login(
    body: LoginRequest = Body(...),
    service: AuthService = Depends(AuthService),
    ip: str = Depends(get_real_ip)
):
    """Обрабатывает вход пользователя в систему и создает сеанс."""
    _user, _session, access_token, refresh_token = await service.authenticate_user(body, ip)

    response = JSONResponse(
        UnifiedResponse(
            status="success", 
            action="login", 
            detail="Login successful."
        ).model_dump()
    )
    _set_auth_cookies(response, access_token, refresh_token)
    return response

@router.post("/logout", status_code=200)
async def logout(
    request: Request,
    service: AuthService = Depends(AuthService),
    user_id: str = Depends(get_current_user_id)
):
    """Обрабатывает выход пользователя из системы и отменяет сеанс."""
    refresh_token = request.cookies.get("refresh_token")
    await service.logout(user_id, refresh_token)
    response = JSONResponse(
        UnifiedResponse(
            status="success", 
            action="logout", 
            detail="Logout successful."
        ).model_dump()
    )
    _delete_auth_cookies(response)
    return response

@router.post(
    "/reset-password", 
    status_code=200, 
    dependencies=[Depends(RateLimiter(times=5, seconds=60))]
)
async def reset_password(
    body: ResetPasswordRequest = Body(...),
    service: AuthService = Depends(AuthService)
):
    """Инициирует процесс сброса пароля."""
    await service.start_password_reset(body.email)
    return JSONResponse(
        UnifiedResponse(
            status="success", 
            action="reset_password", 
            detail="Reset email sent."
        ).model_dump()
    )

@router.post("/complete-reset", status_code=200)
async def complete_reset(
    body: CompleteResetRequest = Body(...),
    service: AuthService = Depends(AuthService)
):
    """Завершает сброс пароля с помощью нового пароля."""
    await service.complete_password_reset(body)
    return JSONResponse(
        UnifiedResponse(
            status="success", 
            action="complete_reset", 
            detail="Password reset completed."
        ).model_dump()
    )

@router.post("/change-password", status_code=200)
async def change_password(
    body: ChangePasswordRequest = Body(...),
    service: AuthService = Depends(AuthService),
    user_id: str = Depends(get_current_user_id)
):
    """Изменяет пароль пользователя после проверки подлинности."""
    await service.change_password(user_id, body)
    return JSONResponse(
        UnifiedResponse(
            status="success", 
            action="change_password", 
            detail="Password changed."
        ).model_dump()
    )

@router.post("/validate-token", status_code=200)
async def validate_token(
    body: TokenValidateRequest = Body(...),
    service: AuthService = Depends(AuthService)
):
    """Проверяет access_token."""
    await service.validate_access_token_async(body.token)
    return JSONResponse(
        UnifiedResponse(
            status="success", 
            action="validate_token", 
            detail="Token valid."
        ).model_dump()
    )

@router.post(
    "/refresh", 
    status_code=200, 
    dependencies=[Depends(RateLimiter(times=30, seconds=60))]
)
async def refresh(
    request: Request,
    service: AuthService = Depends(AuthService)
):
    """Обновляет access_token с помощью refresh_token"""
    access_token = (
        request.cookies.get("access_token")
        or request.headers.get("Authorization", "").replace("Bearer ", "")
    )
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Missing refresh token")
    new_access_token, new_refresh_token = await service.refresh_session(
        refresh_token,
        access_token or "",
    )

    response = JSONResponse(
        UnifiedResponse(
            status="success",
            action="refresh",
            detail="Tokens refreshed.",
        ).model_dump()
    )
    _set_auth_cookies(response, new_access_token, new_refresh_token)
    return response

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
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.backends import default_backend

    public_key_obj = serialization.load_pem_public_key(
        settings.jwt_public_key.encode(),
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