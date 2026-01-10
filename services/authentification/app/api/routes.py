from fastapi import APIRouter, Depends, Header, Query, Body, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from fastapi_limiter.depends import RateLimiter
from functools import lru_cache
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from jwt import decode
from sqlalchemy import text

from app.api import dependencies, middleware
from app.core import exceptions, config
from app.infrastructure.db import models
from app.domain.schemas import api as schemas
from app.services import service
from app.utils import crypto

router = APIRouter(tags=["auth"])
settings = config.settings

def _set_auth_cookies(
    response: Response,
    access_token: str,
    refresh_token: str
):
    """Хелпер для установки httpOnly cookie."""
    secure = (settings.APP.ENV == 'prod')
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
    secure = (settings.APP.ENV == 'prod')
    response.delete_cookie("access_token", httponly=True, secure=secure, samesite='None', path='/')
    response.delete_cookie("refresh_token", httponly=True, secure=secure, samesite='None', path='/')

@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Health check сервиса авторизации"
)
async def health_check(request: Request) -> dict:
    app = request.app
    health_status = {
        "db": "unknown",
        "redis": "unknown",
        "arq": "unknown",
        "dadata": "unknown",
    }
    has_error = False

    engine = getattr(app.state, "engine", None)
    if not engine:
        health_status["db"] = "disconnected"
        has_error = True
    else:
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            health_status["db"] = "ok"
        except Exception:
            health_status["db"] = "failed"
            has_error = True

    arq_pool = getattr(app.state, "arq_pool", None)
    if not arq_pool:
        health_status["arq"] = "disconnected"
        has_error = True
    else:
        try:
            await arq_pool.ping()
            health_status["arq"] = "ok"
        except Exception:
            health_status["arq"] = "failed"
            has_error = True

    dadata_client = getattr(app.state, "dadata_client", None)
    if dadata_client is None:
        health_status["dadata"] = "disabled"
    else:
        health_status["dadata"] = "configured" 

    if has_error:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "error", "components": health_status},
        )

    return {"status": "ok", "components": health_status}


@router.post(
    "/verify-email",
    status_code=200,
    dependencies=[Depends(RateLimiter(times=5, seconds=60))],
    response_model=schemas.UnifiedResponse
)
async def verify_email(
    body: schemas.VerifyEmailRequest = Body(...),
    service: service.AuthService = Depends(dependencies.get_auth_service)
):
    action = await service.start_email_verification(body.email)
    detail = "Complete sign in." if action == "sign_in" else "Verification email sent."
    return schemas.UnifiedResponse(status="success", action=action, detail=detail)


@router.get("/verify-link", status_code=200, response_model=schemas.UnifiedResponse)
async def verify_link(
    token: str = Query(...),
    email: str = Query(...),
    token_type: str = Query(...),
    service: service.AuthService = Depends(dependencies.get_auth_service),
):
    if token_type == 'verification':
        await service.validate_email_verification_token(token, email)
    elif token_type == 'reset':
        await service.validate_password_reset_token(token, email)
    else:
        raise HTTPException(status_code=400, detail="Invalid token type")

    return schemas.UnifiedResponse(status="success", action="verify_link", detail="Token validated.")


@router.post(
    "/complete-registration", 
    status_code=200, 
    dependencies=[Depends(RateLimiter(times=5, seconds=60))],
    response_model=schemas.UnifiedResponse
)
async def complete_registration(
    response: Response,
    body: schemas.CompleteRegistrationRequest = Body(...),
    service: service.AuthService = Depends(dependencies.get_auth_service),
    ip: str = Depends(dependencies.get_real_ip),
    user_agent: str | None = Header(None, alias="User-Agent")
):
    _user, _session, access_token, refresh_token = await service.complete_registration(
        body, ip, user_agent or "Unknown"
    )
    _set_auth_cookies(response, access_token, refresh_token)
    return schemas.UnifiedResponse(status="success", action="complete_registration", detail="Registration completed.")


@router.post(
    "/login", 
    status_code=200, 
    dependencies=[Depends(RateLimiter(times=5, seconds=60))],
    response_model=schemas.UnifiedResponse
)
async def login(
    response: Response,
    body: schemas.LoginRequest = Body(...),
    service: service.AuthService = Depends(dependencies.get_auth_service),
    ip: str = Depends(dependencies.get_real_ip),
    user_agent: str | None = Header(None, alias="User-Agent")
):
    _user, _session, access_token, refresh_token = await service.authenticate_user(
        body, ip, user_agent or "Unknown"
    )
    _set_auth_cookies(response, access_token, refresh_token)
    return schemas.UnifiedResponse(status="success", action="login", detail="Login successful.")


@router.post(
    "/logout", 
    status_code=200,
    response_model=schemas.UnifiedResponse
)
async def logout(
    response: Response,
    request: Request,
    service: service.AuthService = Depends(dependencies.get_auth_service),
    user_id: str | None = Depends(dependencies.get_user_id_from_expired_token)
):
    refresh_token = request.cookies.get("refresh_token")
    if user_id and refresh_token:
        try:
            await service.logout(user_id, refresh_token)
        except exceptions.AuthServiceError as e:
            middleware.logger.warning(f"Failed to revoke session during logout: {e}")

    _delete_auth_cookies(response)
    return schemas.UnifiedResponse(status="success", action="logout", detail="Logout successful.")


@router.post(
    "/reset-password", 
    status_code=200, 
    dependencies=[Depends(RateLimiter(times=5, seconds=60))],
    response_model=schemas.UnifiedResponse
)
async def reset_password(
    body: schemas.ResetPasswordRequest = Body(...),
    service: service.AuthService = Depends(dependencies.get_auth_service)
):
    await service.start_password_reset(body.email)
    return schemas.UnifiedResponse(status="success", action="reset_password", detail="Reset email sent.")


@router.post(
    "/complete-reset", 
    status_code=200,
    response_model=schemas.UnifiedResponse
)
async def complete_reset(
    body: schemas.CompleteResetRequest = Body(...),
    service: service.AuthService = Depends(dependencies.get_auth_service)
):
    await service.complete_password_reset(body)
    return schemas.UnifiedResponse(status="success", action="complete_reset", detail="Password reset completed.")


@router.post(
    "/change-password", 
    status_code=200,
    response_model=schemas.UnifiedResponse
)
async def change_password(
    body: schemas.ChangePasswordRequest = Body(...),
    service: service.AuthService = Depends(dependencies.get_auth_service),
    user: models.User = Depends(dependencies.get_current_active_user)
):
    await service.change_password(user.user_id, body)
    return schemas.UnifiedResponse(status="success", action="change_password", detail="Password changed.")


@router.get("/me", status_code=200, response_model=schemas.UserInfo)
async def get_current_user_info(
    user: models.User = Depends(dependencies.get_current_active_user)
):
    return user


@router.get("/sessions", status_code=200, response_model=schemas.AllSessionsResponse)
async def get_all_user_sessions(
    request: Request,
    service: service.AuthService = Depends(dependencies.get_auth_service),
    user: models.User = Depends(dependencies.get_current_active_user)
):
    current_refresh_token = request.cookies.get("refresh_token")
    sessions_list = await service.get_all_sessions(user.user_id, current_refresh_token)
    return schemas.AllSessionsResponse(sessions=sessions_list)


@router.delete("/sessions/{sessionId}", status_code=200, response_model=schemas.UnifiedResponse)
async def revoke_session(
    sessionId: str,
    service: service.AuthService = Depends(dependencies.get_auth_service),
    user: models.User = Depends(dependencies.get_current_active_user)
):
    await service.revoke_session_by_id(user.user_id, sessionId)
    return schemas.UnifiedResponse(status="success", action="revoke_session", detail="Session has been revoked.")


@router.post(
    "/sessions/logout-others", 
    status_code=200,
    dependencies=[Depends(RateLimiter(times=5, seconds=60))],
    response_model=schemas.UnifiedResponse
)
async def revoke_other_sessions(
    request: Request,
    service: service.AuthService = Depends(dependencies.get_auth_service),
    user: models.User = Depends(dependencies.get_current_active_user)
):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    await service.revoke_other_sessions(user.user_id, refresh_token)
    return schemas.UnifiedResponse(status="success", action="revoke_other_sessions", detail="All other sessions have been revoked.")


@router.post(
    "/validate-token", 
    status_code=200,
    response_model=schemas.UnifiedResponse
)
async def validate_token(
    body: schemas.TokenValidateRequest = Body(...),
    service: service.AuthService = Depends(dependencies.get_auth_service)
):
    await service.validate_access_token(body.token)
    return schemas.UnifiedResponse(status="success", action="validate_token", detail="Token valid.")


@router.post(
    "/refresh", 
    status_code=200, 
    dependencies=[Depends(RateLimiter(times=30, seconds=60))],
    response_model=schemas.UnifiedResponse
)
async def refresh(
    response: Response,
    request: Request,
    service: service.AuthService = Depends(dependencies.get_auth_service)
):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Missing refresh token")
    
    new_access_token, new_refresh_token = await service.refresh_session(refresh_token)
    _set_auth_cookies(response, new_access_token, new_refresh_token)
    return schemas.UnifiedResponse(status="success", action="refresh", detail="Tokens refreshed.")

@lru_cache(maxsize=1)
def _build_jwks() -> dict:
    public_key_obj = serialization.load_pem_public_key(
        settings.JWT.JWT_PUBLIC_KEY.encode(),
        backend=default_backend()
    )
    numbers = public_key_obj.public_numbers()
    return {
        "keys": [{
            "kty": "RSA",
            "use": "sig",
            "kid": "sig-1",
            "alg": "RS256",
            "n": crypto.int_to_base64url(numbers.n),
            "e": crypto.int_to_base64url(numbers.e),
        }]
    }

@router.get("/.well-known/jwks.json")
async def get_jwks():
    return _build_jwks()

@router.get("/gateway-verify", include_in_schema=False)
async def gateway_verify(request: Request):
    """Легковесный эндпоинт для API Gateway."""
    try:
        access_token = request.cookies.get("access_token")
        if not access_token:
            return Response(status_code=401)

        payload = decode(
            access_token,
            settings.JWT.JWT_PUBLIC_KEY,
            algorithms=[settings.JWT.JWT_ALGORITHM],
            issuer="auth-service",
            audience="smart-budget",
            options={"require": ["exp", "sub"]}
        )

        user_id = payload.get("sub")
        if not user_id:
            return Response(status_code=401)

        return Response(status_code=200, headers={"X-User-Id": user_id})
    except Exception:
        return Response(status_code=401)
