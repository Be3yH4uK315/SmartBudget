from fastapi import APIRouter, Depends, Query, Body, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from redis.asyncio import Redis
from uuid import uuid4
from datetime import datetime, timedelta, timezone
from jwt import encode, decode, PyJWTError
from app.dependencies import get_db, get_redis
from app.schemas import (
    VerifyEmailRequest, VerifyLinkRequest, CompleteRegistrationRequest,
    LoginRequest, ResetPasswordRequest, CompleteResetRequest,
    ChangePasswordRequest, TokenValidateRequest, RefreshRequest,
    StatusResponse
)
from app.models import User, Session
from app.utils import parse_device, get_location, hash_token, hash_password, check_password
from app.tasks import send_email_wrapper, send_kafka_event_wrapper
from app.settings import settings
from hashlib import sha256
import sqlalchemy as sa
import base64
import json

router = APIRouter(prefix="", tags=["auth"])

@router.post("/verify-email", status_code=200)
async def verify_email(
    body: VerifyEmailRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    # Проверка существующего пользователя
    existing_user = await db.execute(select(User).where(User.email == body.email)) # type: ignore
    if existing_user.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    token = str(uuid4())
    hashed_token = hash_token(token)
    await redis.set(f"verify:{body.email}", hashed_token, ex=900)  # 15 мин TTL

    send_email_wrapper.delay(
        to=body.email,
        subject="Verify your email for Budget App",
        body=f"Your verification token: {token}. Use it to complete registration."
    )
    return StatusResponse()

@router.get("/verify-link", status_code=200)
async def verify_link(
    token: str = Query(...),
    email: str = Query(...),
    redis: Redis = Depends(get_redis)
):
    hashed_token = hash_token(token)
    stored_hash = await redis.get(f"verify:{email}")
    if not stored_hash or stored_hash.decode() != hashed_token:
        raise HTTPException(status_code=403, detail="Invalid or expired token")
    return StatusResponse()

@router.post("/complete-registration", status_code=200)
async def complete_registration(
    request: Request,
    body: CompleteRegistrationRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    hashed_token = hash_token(body.token)
    stored = await redis.get(f"verify:{body.email}")
    if not stored or stored.decode() != hashed_token:
        raise HTTPException(status_code=403, detail="Invalid or expired token")
    await redis.delete(f"verify:{body.email}")

    device_name = parse_device(body.user_agent)
    ip = request.client.host
    location = get_location(ip)

    pw_hash = hash_password(body.password)

    user = User(
        id=uuid4(),
        role=0,  # Default user role
        email=body.email,
        password_hash=pw_hash,
        name=body.name,
        country=body.country,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.add(user)
    try:
        await db.commit()
        await db.refresh(user)
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Email already registered")

    refresh_token = str(uuid4())
    fingerprint = sha256(refresh_token.encode()).hexdigest()

    session = Session(
        id=uuid4(),
        user_id=user.id,
        user_agent=body.user_agent,
        device_name=device_name,
        ip=ip,
        location=location,
        revoked=False,
        refresh_fingerprint=fingerprint,
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        created_at=datetime.now(timezone.utc)
    )
    db.add(session)
    await db.commit()

    access_payload = {
        "sub": str(user.id),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
        "role": user.role  # int role
    }
    access_token = encode(
        access_payload, 
        settings.jwt_private_key,
        algorithm=settings.jwt_algorithm
    )

    event = {
        "event": "user.registered",
        "user_id": str(user.id),
        "email": body.email,
        "ip": ip,
        "location": location
    }
    send_kafka_event_wrapper.delay("budget.auth.events", event, "AUTH_EVENTS_SCHEMA")

    user_event = {
        "user_id": str(user.id),
        "email": body.email,
        "name": body.name,
        "country": body.country,
        "role": user.role,
        "is_active": True
    }
    send_kafka_event_wrapper.delay("users.active", user_event, "USERS_ACTIVE_SCHEMA")

    response = JSONResponse({"ok": True})
    secure = (settings.env == 'prod')
    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=secure, samesite='strict', max_age=900)
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=secure, samesite='strict', max_age=2592000)
    return response

@router.post("/login", status_code=200, dependencies=[Depends(RateLimiter(times=5, seconds=60))])
async def login(
    request: Request,
    body: LoginRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    fail_key = f"fail:{request.client.host}"
    fails = int(await redis.get(fail_key) or 0)
    if fails >= 5:
        raise HTTPException(status_code=429, detail="Too many attempts, try later")

    user_query = await db.execute(select(User).where(User.email == body.email, User.is_active == sa.true())) # type: ignore
    user = user_query.scalar_one_or_none()
    if not user or not check_password(body.password, user.password_hash):
        await redis.incr(fail_key)
        await redis.expire(fail_key, 300)  # 5 min lock after 5 fails
        raise HTTPException(status_code=403, detail="Invalid credentials")

    await redis.delete(fail_key)

    device_name = parse_device(body.user_agent)
    ip = request.client.host
    location = get_location(ip)

    refresh_token = str(uuid4())
    fingerprint = sha256(refresh_token.encode()).hexdigest()
    session = Session(
        id=uuid4(),
        user_id=user.id,
        user_agent=body.user_agent,
        device_name=device_name,
        ip=ip,
        location=location,
        revoked=False,
        refresh_fingerprint=fingerprint,
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        created_at=datetime.now(timezone.utc)
    )
    db.add(session)
    user.last_login = datetime.now(timezone.utc)
    await db.commit()

    access_payload = {
        "sub": str(user.id),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
        "role": user.role  # int role
    }
    access_token = encode(
        access_payload, 
        settings.jwt_private_key,
        algorithm=settings.jwt_algorithm
    )

    event = {"event": "user.login", "user_id": str(user.id), "ip": ip, "location": location}
    send_kafka_event_wrapper.delay("budget.auth.events", event, "AUTH_EVENTS_SCHEMA")

    response = JSONResponse({"ok": True})
    secure = (settings.env == 'prod')
    response.set_cookie("access_token", access_token, httponly=True, secure=secure, samesite='strict', max_age=900)
    response.set_cookie("refresh_token", refresh_token, httponly=True, secure=secure, samesite='strict', max_age=2592000)
    return response

@router.post("/logout", status_code=200)
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        response.delete_cookie("access_token")
        raise HTTPException(status_code=401, detail="Not authenticated")
    fingerprint = sha256(refresh_token.encode()).hexdigest()
    session_query = await db.execute(select(Session).where(
        Session.refresh_fingerprint == fingerprint, 
        Session.revoked == sa.false()
    ))
    session = session_query.scalar_one_or_none()
    if not session:
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        raise HTTPException(status_code=404, detail="Session not found")
    session.revoked = True
    user_id_for_event = session.user_id
    await db.commit()
    event = {"event": "user.logout", "user_id": str(user_id_for_event)}
    send_kafka_event_wrapper.delay("budget.auth.events", event, "AUTH_EVENTS_SCHEMA")
    secure = (settings.env == 'prod')
    response.delete_cookie("access_token", httponly=True, secure=secure, samesite='strict')
    response.delete_cookie("refresh_token", httponly=True, secure=secure, samesite='strict')
    
    return StatusResponse()

@router.post("/reset-password", status_code=200, dependencies=[Depends(RateLimiter(times=5, seconds=60))])
async def reset_password(
    body: ResetPasswordRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    user_query = await db.execute(select(User).where(User.email == body.email)) # type: ignore
    user = user_query.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    token = str(uuid4())
    hashed_token = hash_token(token)
    await redis.set(f"reset:{body.email}", hashed_token, ex=900)

    send_email_wrapper.delay(
        to=body.email,
        subject="Reset your password",
        body=f"Your reset token: {token}"
    )
    return StatusResponse()

@router.post("/complete-reset", status_code=200)
async def complete_reset(
    body: CompleteResetRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    hashed_token = hash_token(body.token)
    stored = await redis.get(f"reset:{body.email}")
    if not stored or stored.decode() != hashed_token:
        raise HTTPException(status_code=403, detail="Invalid token")
    await redis.delete(f"reset:{body.email}")

    pw_hash = hash_password(body.new_password)

    user_query = await db.execute(select(User).where(User.email == body.email)) # type: ignore
    user = user_query.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.password_hash = pw_hash
    await db.commit()

    event = {"event": "user.password_reset", "user_id": str(user.id)}
    send_kafka_event_wrapper.delay("budget.auth.events", event, "AUTH_EVENTS_SCHEMA")
    return StatusResponse()

@router.post("/change-password", status_code=200)
async def change_password(
    body: ChangePasswordRequest = Body(...),
    db: AsyncSession = Depends(get_db)
):
    user_query = await db.execute(select(User).where(User.id == body.user_id)) # type: ignore
    user = user_query.scalar_one_or_none()
    if not user or not check_password(body.password, user.password_hash):
        raise HTTPException(status_code=403, detail="Invalid current password")

    pw_hash = hash_password(body.new_password)
    user.password_hash = pw_hash
    await db.commit()

    event = {"event": "user.password_changed", "user_id": str(body.user_id)}
    send_kafka_event_wrapper.delay("budget.auth.events", event, "AUTH_EVENTS_SCHEMA")
    return StatusResponse()

@router.post("/validate-token", status_code=200)
async def validate_token(
    body: TokenValidateRequest = Body(...),
):
    try:
        payload = decode(
            body.token, 
            settings.jwt_public_key,
            algorithms=[settings.jwt_algorithm]
        )
        if "sub" not in payload:
            raise PyJWTError("Missing sub")
        return StatusResponse()
    except PyJWTError:
        event = {"event": "user.token_invalid", "token": "anonymized"}
        send_kafka_event_wrapper.delay("budget.auth.events", event, "AUTH_EVENTS_SCHEMA")
        raise HTTPException(status_code=401, detail="Invalid token")

@router.post("/refresh", status_code=200)
async def refresh(
    request: Request,
    body: RefreshRequest = Body(...),
    db: AsyncSession = Depends(get_db)
):
    access_token = request.cookies.get("access_token") or request.headers.get("Authorization", "").replace("Bearer ", "")
    if not access_token:
        raise HTTPException(status_code=401, detail="Missing access token")

    try:
        payload = decode(access_token, settings.jwt_public_key, algorithms=[settings.jwt_algorithm], options={"verify_exp": False})
        user_id = payload.get("sub")
        if not user_id:
            raise PyJWTError("Missing sub")
    except PyJWTError as e:
        raise HTTPException(status_code=401, detail="Invalid access token")

    fingerprint = sha256(body.refresh_token.encode()).hexdigest()
    session_query = await db.execute(select(Session).where(
        Session.user_id == user_id, # type: ignore
        Session.refresh_fingerprint == fingerprint, # type: ignore
        Session.revoked == sa.false(),# type: ignore
        Session.expires_at > datetime.now(timezone.utc)
    ))
    session = session_query.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=403, detail="Invalid refresh token")

    access_payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
        "role": (await db.execute(select(User.role).where(User.id == user_id))).scalar() # type: ignore
    }
    access_token = encode(
        access_payload, 
        settings.jwt_private_key,
        algorithm=settings.jwt_algorithm
    )

    response = JSONResponse({"ok": True})
    secure = (settings.env == 'prod')
    response.set_cookie("access_token", access_token, httponly=True, secure=secure, samesite='strict', max_age=900)
    return response

def _int_to_base64url(value: int) -> str:
    byte_len = (value.bit_length() + 7) // 8
    bytes_val = value.to_bytes(byte_len, "big")
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