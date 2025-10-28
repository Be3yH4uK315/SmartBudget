from fastapi import APIRouter, Depends, Query, Body, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from fastapi_limiter.depends import RateLimiter
import base64

from app.schemas import (
    VerifyEmailRequest, VerifyLinkRequest, CompleteRegistrationRequest,
    LoginRequest, ResetPasswordRequest, CompleteResetRequest,
    ChangePasswordRequest, TokenValidateRequest, RefreshRequest,
    StatusResponse
)
from app.settings import settings
from app.services import AuthService

router = APIRouter(prefix="", tags=["auth"])

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
        htt_only=True, 
        secure=secure, 
        samesite='strict', 
        max_age=900 # 15 min
    )
    response.set_cookie(
        key="refresh_token", 
        value=refresh_token, 
        htt_only=True, 
        secure=secure, 
        samesite='strict', 
        max_age=2592000 # 30 days
    )

def _delete_auth_cookies(response: Response):
    """Хелпер для удаления auth cookie."""
    secure = (settings.env == 'prod')
    response.delete_cookie("access_token", htt_only=True, secure=secure, samesite='strict')
    response.delete_cookie("refresh_token", htt_only=True, secure=secure, samesite='strict')


@router.post("/verify-email", status_code=200)
async def verify_email(
    body: VerifyEmailRequest = Body(...),
    service: AuthService = Depends(AuthService)
):
    await service.start_email_verification(body.email)
    return StatusResponse()

@router.get("/verify-link", status_code=200)
async def verify_link(
    token: str = Query(...),
    email: str = Query(...),
    service: AuthService = Depends(AuthService)
):
    await service.validate_verification_token(token, email)
    return StatusResponse()

@router.post("/complete-registration", status_code=200)
async def complete_registration(
    request: Request,
    body: CompleteRegistrationRequest = Body(...),
    service: AuthService = Depends(AuthService)
):
    _user, _session, access_token, refresh_token = \
        await service.complete_registration(body, request.client.host if request.client else "127.0.0.1")

    response = JSONResponse({"ok": True})
    _set_auth_cookies(response, access_token, refresh_token)
    return response

@router.post("/login", status_code=200, dependencies=[Depends(RateLimiter(times=5, seconds=60))])
async def login(
    request: Request,
    body: LoginRequest = Body(...),
    service: AuthService = Depends(AuthService)
):
    _user, _session, access_token, refresh_token = \
        await service.authenticate_user(body, request.client.host if request.client else "127.0.0.1")

    response = JSONResponse({"ok": True})
    _set_auth_cookies(response, access_token, refresh_token)
    return response

@router.post("/logout", status_code=200)
async def logout(
    request: Request,
    response: Response,
    service: AuthService = Depends(AuthService)
):
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        try:
            await service.logout(refresh_token)
        except HTTPException as e:
            if e.status_code == 404:
                _delete_auth_cookies(response)
            raise e
    
    _delete_auth_cookies(response)
    if not refresh_token:
        _delete_auth_cookies(response)

    return StatusResponse()

@router.post("/reset-password", status_code=200, dependencies=[Depends(RateLimiter(times=5, seconds=60))])
async def reset_password(
    body: ResetPasswordRequest = Body(...),
    service: AuthService = Depends(AuthService)
):
    await service.start_password_reset(body.email)
    return StatusResponse()

@router.post("/complete-reset", status_code=200)
async def complete_reset(
    body: CompleteResetRequest = Body(...),
    service: AuthService = Depends(AuthService)
):
    await service.complete_password_reset(body)
    return StatusResponse()

@router.post("/change-password", status_code=200)
async def change_password(
    body: ChangePasswordRequest = Body(...),
    service: AuthService = Depends(AuthService)
):
    await service.change_password(body)
    return StatusResponse()

@router.post("/validate-token", status_code=200)
async def validate_token(
    body: TokenValidateRequest = Body(...),
    service: AuthService = Depends(AuthService)
):
    service.validate_access_token(body.token)
    return StatusResponse()

@router.post("/refresh", status_code=200)
async def refresh(
    request: Request,
    body: RefreshRequest = Body(...),
    service: AuthService = Depends(AuthService)
):
    access_token = request.cookies.get("access_token") or \
                   request.headers.get("Authorization", "").replace("Bearer ", "")
    
    new_access_token = await service.refresh_session(
        body.refresh_token, 
        access_token or ""
    )

    response = JSONResponse({"ok": True})
    secure = (settings.env == 'prod')
    response.set_cookie(
        "access_token", 
        new_access_token, 
        htt_only=True, 
        secure=secure, 
        samesite='strict', 
        max_age=900
    )
    return response

def _int_to_base64url(value: int) -> str:
    byte_len = (value.bit_length() + 7) // 8
    if byte_len == 0:
        byte_len = 1
    bytes_val = value.to_bytes(byte_len, "big", signed=False)
    return base64.urlsafe_b64encode(bytes_val).decode("utf-8").rstrip("=")

@router.get("/.well-known/jwks.json")
async def get_jwks():
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