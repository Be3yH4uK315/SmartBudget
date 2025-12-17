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

def _setAuthCookies(
    response: Response,
    accessToken: str,
    refreshToken: str
):
    """Хелпер для установки httpOnly cookie."""
    secure = (settings.settings.APP.ENV == 'prod')
    response.set_cookie(
        key="access_token",
        value=accessToken,
        httponly=True,
        secure=secure,
        samesite='None',
        path='/',
        max_age=900,  # 15 min
    )
    response.set_cookie(
        key="refresh_token",
        value=refreshToken,
        httponly=True,
        secure=secure,
        samesite='None',
        path='/',
        max_age=2592000,  # 30 days
    )

def _deleteAuthCookies(response: Response):
    """Хелпер для удаления auth cookie."""
    secure = (settings.settings.APP.ENV == 'prod')
    response.delete_cookie("access_token", httponly=True, secure=secure, samesite='None', path='/')
    response.delete_cookie("refresh_token", httponly=True, secure=secure, samesite='None', path='/')


@router.post(
    "/verify-email",
    status_code=200,
    dependencies=[Depends(RateLimiter(times=5, seconds=60))],
    response_model=schemas.UnifiedResponse
)
async def verifyEmail(
    body: schemas.VerifyEmailRequest = Body(...),
    service: services.AuthService = Depends(services.AuthService)
):
    """Инициирует процесс проверки электронной почты."""
    action = await service.startEmailVerification(body.email)
    detail = "Complete sign in." if action == "sign_in" else "Verification email sent."
    return schemas.UnifiedResponse(
        status="success", 
        action=action, 
        detail=detail
    )

@router.get("/verify-link", status_code=200, response_model=schemas.UnifiedResponse)
async def verifyLink(
    token: str = Query(...),
    email: str = Query(...),
    tokenType: str = Query(...),
    service: services.AuthService = Depends(services.AuthService),
):
    """Проверяет токен подтверждения по ссылке электронной почты."""
    if tokenType == 'verification':
        await service.validateEmailVerificationToken(token, email)
    elif tokenType == 'reset':
        await service.validatePasswordResetToken(token, email)
    else:
        raise HTTPException(status_code=400, detail="Invalid token type")

    return schemas.UnifiedResponse(
        status="success",
        action="verifyLink",
        detail="Token validated.",
    )

@router.post(
    "/complete-registration", 
    status_code=200, 
    dependencies=[Depends(RateLimiter(times=5, seconds=60))],
    response_model=schemas.UnifiedResponse
)
async def completeRegistration(
    response: Response,
    body: schemas.CompleteRegistrationRequest = Body(...),
    service: services.AuthService = Depends(services.AuthService),
    ip: str = Depends(dependencies.getRealIp),
    userAgent: str | None = Header(None, alias="User-Agent")
):
    """Завершает регистрацию пользователя после верификации."""
    _user, _session, accessToken, refreshToken = await service.completeRegistration(
        body, 
        ip, 
        userAgent or "Unknown"
    )

    _setAuthCookies(response, accessToken, refreshToken)
    
    return schemas.UnifiedResponse(
        status="success", 
        action="completeRegistration", 
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
    ip: str = Depends(dependencies.getRealIp),
    userAgent: str | None = Header(None, alias="User-Agent")
):
    """Обрабатывает вход пользователя в систему и создает сеанс."""
    _user, _session, accessToken, refreshToken = await service.authenticateUser(
        body, 
        ip, 
        userAgent or "Unknown"
    )

    _setAuthCookies(response, accessToken, refreshToken)

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
    userId: str | None = Depends(dependencies.getUserIdFromExpiredToken)
):
    """Обрабатывает выход пользователя из системы и отменяет сеанс."""
    refreshToken = request.cookies.get("refresh_token")
    if userId and refreshToken:
        try:
            await service.logout(userId, refreshToken)
        except exceptions.AuthServiceError as e:
            middleware.logger.warning(f"Failed to revoke session during logout: {e}")

    _deleteAuthCookies(response)

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
async def resetPassword(
    body: schemas.ResetPasswordRequest = Body(...),
    service: services.AuthService = Depends(services.AuthService)
):
    """Инициирует процесс сброса пароля."""
    await service.startPasswordReset(body.email)

    return schemas.UnifiedResponse(
        status="success", 
        action="resetPassword", 
        detail="Reset email sent."
    )

@router.post(
    "/complete-reset", 
    status_code=200,
    response_model=schemas.UnifiedResponse
)
async def completeReset(
    body: schemas.CompleteResetRequest = Body(...),
    service: services.AuthService = Depends(services.AuthService)
):
    """Завершает сброс пароля с помощью нового пароля."""
    await service.completePasswordReset(body)

    return schemas.UnifiedResponse(
        status="success", 
        action="completeReset", 
        detail="Password reset completed."
    )

@router.post(
    "/change-password", 
    status_code=200,
    response_model=schemas.UnifiedResponse
)
async def changePassword(
    body: schemas.ChangePasswordRequest = Body(...),
    service: services.AuthService = Depends(services.AuthService),
    user: models.User = Depends(dependencies.getCurrentActiveUser)
):
    """Изменяет пароль пользователя после проверки подлинности."""
    await service.changePassword(user.userId, body)

    return schemas.UnifiedResponse(
        status="success", 
        action="changePassword", 
        detail="Password changed."
    )

@router.get("/me", status_code=200, response_model=schemas.UserInfo)
async def getCurrentUserInfo(
    user: models.User = Depends(dependencies.getCurrentActiveUser)
):
    """Возвращает информацию о текущем аутентифицированном пользователе."""
    return user

@router.get(
    "/sessions",
    status_code=200,
    response_model=schemas.AllSessionsResponse
)
async def getAllUserSessions(
    request: Request,
    service: services.AuthService = Depends(services.AuthService),
    user: models.User = Depends(dependencies.getCurrentActiveUser)
):
    """Получает список всех активных сессий для текущего пользователя."""
    currentRefreshToken = request.cookies.get("refresh_token")
    sessionsList = await service.getAllSessions(user.userId, currentRefreshToken)
    return schemas.AllSessionsResponse(sessions=sessionsList)


@router.delete(
    "/sessions/{sessionId}", 
    status_code=200,
    response_model=schemas.UnifiedResponse
)
async def revokeSession(
    sessionId: UUID,
    service: services.AuthService = Depends(services.AuthService),
    user: models.User = Depends(dependencies.getCurrentActiveUser)
):
    """Отзывает одну конкретную сессию по ее ID."""
    await service.revokeSessionById(user.userId, sessionId)

    return schemas.UnifiedResponse(
        status="success",
        action="revokeSession",
        detail="Session has been revoked."
    )


@router.post(
    "/sessions/logout-others", 
    status_code=200,
    dependencies=[Depends(RateLimiter(times=5, seconds=60))],
    response_model=schemas.UnifiedResponse
)
async def revokeOtherSessions(
    request: Request,
    service: services.AuthService = Depends(services.AuthService),
    user: models.User = Depends(dependencies.getCurrentActiveUser)
):
    """Отзывает все сессии, кроме текущей."""
    refreshToken = request.cookies.get("refresh_token")
    if not refreshToken:
        raise HTTPException(status_code=401, detail="Not authenticated")

    await service.revokeOtherSessions(user.userId, refreshToken)

    return schemas.UnifiedResponse(
        status="success",
        action="revokeOtherSessions",
        detail="All other sessions have been revoked."
    )

@router.post(
    "/validate-token", 
    status_code=200,
    response_model=schemas.UnifiedResponse
)
async def validateToken(
    body: schemas.TokenValidateRequest = Body(...),
    service: services.AuthService = Depends(services.AuthService)
):
    """Проверяет access_token."""
    await service.validateAccessToken(body.token)

    return schemas.UnifiedResponse(
        status="success", 
        action="validateToken", 
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
    refreshToken = request.cookies.get("refresh_token")
    if not refreshToken:
        raise HTTPException(status_code=401, detail="Missing refresh token")
    newAccessToken, newRefreshToken = await service.refreshSession(refreshToken)

    _setAuthCookies(response, newAccessToken, newRefreshToken)

    return schemas.UnifiedResponse(
        status="success",
        action="refresh",
        detail="Tokens refreshed.",
    )

def _intToBase64url(value: int) -> str:
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
    publicKeyObj = serialization.load_pem_public_key(
        settings.settings.JWT.JWT_PUBLIC_KEY.encode(),
        backend=default_backend()
    )
    public_numbers = publicKeyObj.public_numbers()

    jwks = {
        "keys": [
            {
                "kty": "RSA",
                "use": "sig",
                "kid": "sig-1",
                "alg": "RS256",
                "n": _intToBase64url(public_numbers.n),
                "e": _intToBase64url(public_numbers.e),
            }
        ]
    }
    return jwks