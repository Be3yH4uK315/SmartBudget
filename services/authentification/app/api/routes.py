from uuid import UUID
from fastapi import APIRouter, Depends, Header, Query, Body, HTTPException, Request, Response, status
from fastapi.responses import ORJSONResponse
from fastapi_limiter.depends import RateLimiter
from functools import lru_cache
from sqlalchemy import text

from app.api import dependencies, middleware
from app.core import exceptions, config
from app.infrastructure.db import models
from app.domain.schemas import api as schemas
from app.domain.schemas import dtos
from app.services.registration_service import RegistrationService
from app.services.login_service import LoginService
from app.services.password_service import PasswordService
from app.services.session_service import SessionService
from app.services.token_service import TokenService
from app.utils import cookies

router = APIRouter(tags=["auth"])
settings = config.settings

@router.get(
    "/health/live",
    status_code=status.HTTP_200_OK,
    summary="Liveness probe"
)
async def liveness_check() -> dict:
    """Легкая проверка."""
    return {"status": "ok"}

@router.get(
    "/health/ready",
    status_code=status.HTTP_200_OK,
    summary="Readiness probe"
)
async def readiness_check(request: Request) -> Response:
    """Тяжелая проверка. Проверяет зависимости."""
    app = request.app
    health_status = {
        "db": "unknown",
        "redis": "unknown",
        "arq": "unknown",
        "kafka": "unknown",
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

    kafka_producer = getattr(app.state, "kafka_producer", None)
    if not kafka_producer:
        health_status["kafka"] = "disconnected"
        has_error = True
    else:
        try:
            if kafka_producer._is_running:
                health_status["kafka"] = "ok"
            else:
                health_status["kafka"] = "not_running"
                has_error = True
        except Exception:
            health_status["kafka"] = "failed"
            has_error = True

    if has_error:
        return ORJSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", "components": health_status},
        )

    return ORJSONResponse(content={"status": "ready", "components": health_status})

@router.post(
    "/verify-email",
    status_code=200,
    dependencies=[Depends(RateLimiter(times=5, seconds=60))],
    response_model=schemas.UnifiedResponse
)
async def verify_email(
    body: schemas.VerifyEmailRequest = Body(...),
    reg_service: RegistrationService = Depends(dependencies.get_registration_service)
):
    action = await reg_service.start_email_verification(body.email)
    detail = "Complete sign in." if action == "sign_in" else "Verification email sent."
    return schemas.UnifiedResponse(status="success", action=action, detail=detail)


@router.get(
    "/verify-link",
    status_code=200,
    dependencies=[Depends(RateLimiter(times=5, seconds=60))],
    response_model=schemas.UnifiedResponse
)
async def verify_link(
    token: str = Query(...),
    email: str = Query(...),
    tokenType: str = Query(...),
    reg_service: RegistrationService = Depends(dependencies.get_registration_service),
    pwd_service: PasswordService = Depends(dependencies.get_password_service)
):
    if tokenType == 'verification':
        await reg_service.validate_email_verification_token(token, email)
    elif tokenType == 'reset':
        await pwd_service.validate_password_reset_token(token, email)
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
    reg_service: RegistrationService = Depends(dependencies.get_registration_service),
    ip: str = Depends(dependencies.get_real_ip),
    user_agent: str | None = Header(None, alias="User-Agent")
):
    _user, _session, access_token, refresh_token = await reg_service.complete_registration(
        body, ip, user_agent or "Unknown"
    )
    cookies.set_auth_cookies(response, access_token, refresh_token)
    return schemas.UnifiedResponse(status="success", action="completeRegistration", detail="Registration completed.")


@router.post(
    "/login", 
    status_code=200, 
    dependencies=[Depends(RateLimiter(times=5, seconds=60))],
    response_model=schemas.UnifiedResponse
)
async def login(
    response: Response,
    body: schemas.LoginRequest = Body(...),
    login_service: LoginService = Depends(dependencies.get_login_service),
    ip: str = Depends(dependencies.get_real_ip),
    user_agent: str | None = Header(None, alias="User-Agent")
):
    _user, _session, access_token, refresh_token = await login_service.authenticate_user(
        body, ip, user_agent or "Unknown"
    )
    cookies.set_auth_cookies(response, access_token, refresh_token)
    return schemas.UnifiedResponse(status="success", action="login", detail="Login successful.")


@router.post(
    "/logout", 
    status_code=200,
    response_model=schemas.UnifiedResponse
)
async def logout(
    response: Response,
    request: Request,
    login_service: LoginService = Depends(dependencies.get_login_service),
    user_id: str | None = Depends(dependencies.get_user_id_from_expired_token)
):
    refresh_token = request.cookies.get("refresh_token")
    if user_id and refresh_token:
        try:
            await login_service.logout(user_id, refresh_token)
        except exceptions.AuthServiceError as e:
            middleware.logger.warning(f"Failed to revoke session during logout: {e}")

    cookies.delete_auth_cookies(response)
    return schemas.UnifiedResponse(status="success", action="logout", detail="Logout successful.")


@router.post(
    "/reset-password", 
    status_code=200, 
    dependencies=[Depends(RateLimiter(times=5, seconds=60))],
    response_model=schemas.UnifiedResponse
)
async def reset_password(
    body: schemas.ResetPasswordRequest = Body(...),
    pwd_service: PasswordService = Depends(dependencies.get_password_service)
):
    await pwd_service.start_password_reset(body.email)
    return schemas.UnifiedResponse(status="success", action="resetPassword", detail="Reset email sent.")


@router.post(
    "/complete-reset", 
    status_code=200,
    response_model=schemas.UnifiedResponse
)
async def complete_reset(
    body: schemas.CompleteResetRequest = Body(...),
    pwd_service: PasswordService = Depends(dependencies.get_password_service)
):
    await pwd_service.complete_password_reset(body)
    return schemas.UnifiedResponse(status="success", action="completeReset", detail="Password reset completed.")


@router.post("/change-password", status_code=200, response_model=schemas.UnifiedResponse)
async def change_password(
    body: schemas.ChangePasswordRequest = Body(...),
    pwd_service: PasswordService = Depends(dependencies.get_password_service),
    user: dtos.UserDTO = Depends(dependencies.get_current_active_user)
):
    await pwd_service.change_password(user.user_id, body)
    return schemas.UnifiedResponse(status="success", action="changePassword", detail="Password changed.")


@router.get("/me", status_code=200, response_model=schemas.UserInfo)
async def get_current_user_info(
    user: dtos.UserDTO = Depends(dependencies.get_current_active_user)
):
    return user


@router.patch(
    "/me/retention", 
    status_code=200, 
    response_model=schemas.UnifiedResponse
)
async def update_retention_settings(
    body: schemas.UpdateRetentionRequest,
    session_service: SessionService = Depends(dependencies.get_session_service),
    user: dtos.UserDTO = Depends(dependencies.get_current_active_user)
):
    await session_service.update_user_retention_settings(user.user_id, body.days)
    
    return schemas.UnifiedResponse(
        status="success", 
        action="updateRetention", 
        detail=f"Session retention updated to {body.days} days."
    )


@router.get("/sessions", status_code=200, response_model=schemas.AllSessionsResponse)
async def get_all_user_sessions(
    request: Request,
    session_service: SessionService = Depends(dependencies.get_session_service),
    user: dtos.UserDTO = Depends(dependencies.get_current_active_user)
):
    current_refresh_token = request.cookies.get("refresh_token")
    sessions_list = await session_service.get_all_sessions(user.user_id, current_refresh_token)
    return schemas.AllSessionsResponse(sessions=sessions_list)


@router.delete("/sessions/{sessionId}", status_code=200, response_model=schemas.UnifiedResponse)
async def revoke_session(
    sessionId: str,
    session_service: SessionService = Depends(dependencies.get_session_service),
    user: dtos.UserDTO = Depends(dependencies.get_current_active_user)
):
    await session_service.revoke_session(user.user_id, UUID(sessionId))
    return schemas.UnifiedResponse(status="success", action="revokeSession", detail="Session has been revoked.")


@router.post(
    "/sessions/logout-others", 
    status_code=200,
    dependencies=[Depends(RateLimiter(times=5, seconds=60))],
    response_model=schemas.UnifiedResponse
)
async def revoke_other_sessions(
    request: Request,
    session_service: SessionService = Depends(dependencies.get_session_service),
    user: models.User = Depends(dependencies.get_current_active_user)
):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    await session_service.revoke_other_sessions(user.user_id, refresh_token)
    return schemas.UnifiedResponse(status="success", action="revokeOtherSessions", detail="All other sessions have been revoked.")


@router.post(
    "/validate-token", 
    status_code=200,
    response_model=schemas.UnifiedResponse
)
async def validate_token(
    body: schemas.TokenValidateRequest = Body(...),
    session_service: SessionService = Depends(dependencies.get_session_service)
):
    await session_service.validate_access_token(body.token)
    return schemas.UnifiedResponse(status="success", action="validateToken", detail="Token valid.")


@router.post(
    "/refresh", 
    status_code=200, 
    dependencies=[Depends(RateLimiter(times=30, seconds=60))],
    response_model=schemas.UnifiedResponse
)
async def refresh(
    response: Response,
    request: Request,
    session_service: SessionService = Depends(dependencies.get_session_service)
):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Missing refresh token")
    
    new_access_token, new_refresh_token = await session_service.refresh_session(refresh_token)
    cookies.set_auth_cookies(response, new_access_token, new_refresh_token)
    return schemas.UnifiedResponse(status="success", action="refresh", detail="Tokens refreshed.")

@router.get("/.well-known/jwks.json")
async def get_jwks(
    token_service: TokenService = Depends(dependencies.get_token_service)
):
    return _get_cached_jwks(token_service)

@lru_cache(maxsize=1)
def _get_cached_jwks(service: TokenService):
    return service.get_jwks()

@router.get("/gateway-verify", include_in_schema=False)
async def gateway_verify(
    request: Request, 
    token_service: TokenService = Depends(dependencies.get_token_service),
    session_service: SessionService = Depends(dependencies.get_session_service)
):
    """Легковесный эндпоинт для API Gateway."""
    access_token = request.cookies.get("access_token")
    if not access_token:
        return Response(status_code=401)

    try:
        payload = await token_service.decode_token(access_token, verify_exp=True)
        
        user_id = payload.get("sub")
        session_id = payload.get("sid")

        if not user_id or not session_id:
             return Response(status_code=401)

        is_valid = await session_service.verify_session_fast(session_id)
        
        if not is_valid:
            return Response(status_code=401)

        return Response(status_code=200, headers={"X-User-Id": user_id})

    except Exception:
        return Response(status_code=401)