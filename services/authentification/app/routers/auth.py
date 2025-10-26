from fastapi import APIRouter, Depends, Query, Body, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from redis.asyncio import Redis
from uuid import uuid4
from datetime import datetime, timedelta
from jwt import encode, decode, PyJWTError
from app.dependencies import get_db, get_redis
from app.schemas import (
    VerifyEmailRequest, VerifyLinkRequest, CompleteRegistrationRequest,
    LoginRequest, LogoutRequest, ResetPasswordRequest, CompleteResetRequest,
    ChangePasswordRequest, TokenValidateRequest, RefreshRequest
)
from app.models import User, Session, Role
from app.utils import parse_device, get_location, hash_token, hash_password, check_password
from app.kafka import send_event, AUTH_EVENTS_SCHEMA, USERS_ACTIVE_SCHEMA
from app.tasks import send_email_wrapper
from app.settings import settings
from hashlib import sha256

router = APIRouter(prefix="", tags=["auth"])

# Инициализация limiter будет в main.py

@router.post("/verify-email", status_code=200)
async def verify_email(
    request: VerifyEmailRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    existing_user = await db.execute(select(User).where(User.email == request.email))
    if existing_user.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    token = str(uuid4())
    hashed_token = hash_token(token)
    await redis.set(f"verify:{request.email}", hashed_token, ex=900)  # 15 мин TTL

    # Асинхронная отправка email через Celery
    send_email_wrapper.delay(
        to=request.email,
        subject="Verify your email for Budget App",
        body=f"Your verification token: {token}. Use it to complete registration."
    )
    return {"ok": True}

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
    return {"ok": True}

@router.post("/complete-registration", status_code=200)
async def complete_registration(
    request: Request,
    body: CompleteRegistrationRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    email = body.email if hasattr(body, 'email') else "from_previous_step"
    hashed_token = hash_token(body.token)
    stored = await redis.get(f"verify:{email}")
    if not stored or stored.decode() != hashed_token:
        raise HTTPException(status_code=403, detail="Invalid or expired token")
    await redis.delete(f"verify:{email}")

    device_name = parse_device(body.user_agent)
    ip = request.client.host
    location = get_location(ip)

    pw_hash = hash_password(body.password)

    default_role_query = await db.execute(select(Role).where(Role.name == 'user'))
    default_role = default_role_query.scalar_one_or_none()
    if not default_role:
        raise HTTPException(status_code=500, detail="Default role not found")

    user = User(
        id=uuid4(),
        role_id=default_role.id,
        email=email,
        password_hash=pw_hash,
        name=body.name,
        country=body.country,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

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
        expires_at=datetime.utcnow() + timedelta(days=30),
        created_at=datetime.utcnow()
    )
    db.add(session)
    await db.commit()

    access_payload = {
        "sub": str(user.id),
        "exp": datetime.utcnow() + timedelta(minutes=15),
        "role": default_role.name
    }
    access_token = encode(access_payload, settings.jwt_secret, algorithm="HS256")

    # Публикация событий в Kafka
    event = {
        "event": "user.registered",
        "user_id": str(user.id),
        "email": email,
        "name": body.name
    }
    await send_event("budget.auth.events", event, AUTH_EVENTS_SCHEMA)

    user_event = {
        "user_id": str(user.id),
        "email": email,
        "name": body.name,
        "country": body.country,
        "role_id": str(default_role.id),
        "is_active": True
    }
    await send_event("users.active", user_event, USERS_ACTIVE_SCHEMA)

    response = JSONResponse({"ok": True})
    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=True, samesite='strict', max_age=900)
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=True, samesite='strict', max_age=2592000)
    return response

@router.post("/login", status_code=200, dependencies=[Depends(RateLimiter(times=5, seconds=60))])
async def login(
    request: Request,
    body: LoginRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    user_query = await db.execute(select(User).where(User.email == body.email, User.is_active == True))
    user = user_query.scalar_one_or_none()
    if not user or not check_password(body.password, user.password_hash):
        fail_key = f"fail:{request.client.host}"
        fails = await redis.incr(fail_key)
        if fails > 5:
            await redis.expire(fail_key, 300)  # Lock 5 min
            raise HTTPException(status_code=429, detail="Too many attempts")
        raise HTTPException(status_code=403, detail="Invalid credentials")

    await redis.delete(f"fail:{request.client.host}")

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
        expires_at=datetime.utcnow() + timedelta(days=30),
        created_at=datetime.utcnow()
    )
    db.add(session)
    user.last_login = datetime.utcnow()
    await db.commit()

    access_payload = {
        "sub": str(user.id),
        "exp": datetime.utcnow() + timedelta(minutes=15),
        "role": (await db.execute(select(Role.name).where(Role.id == user.role_id))).scalar()
    }
    access_token = encode(access_payload, settings.jwt_secret, algorithm="HS256")

    event = {"event": "user.login", "user_id": str(user.id), "ip": ip, "location": location}
    await send_event("budget.auth.events", event, AUTH_EVENTS_SCHEMA)

    response = JSONResponse({"ok": True})
    response.set_cookie("access_token", access_token, httponly=True, secure=True, samesite='strict', max_age=900)
    response.set_cookie("refresh_token", refresh_token, httponly=True, secure=True, samesite='strict', max_age=2592000)
    return response

@router.post("/logout", status_code=200)
async def logout(
    body: LogoutRequest = Body(...),
    db: AsyncSession = Depends(get_db)
):
    session_query = await db.execute(select(Session).where(Session.user_id == body.user_id, Session.user_agent == body.user_agent, Session.revoked == False))
    session = session_query.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.revoked = True
    await db.commit()

    event = {"event": "user.logout", "user_id": str(body.user_id)}
    await send_event("budget.auth.events", event, AUTH_EVENTS_SCHEMA)

    response = JSONResponse({"ok": True})
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return response

@router.post("/reset-password", status_code=200, dependencies=[Depends(RateLimiter(times=5, seconds=60))])
async def reset_password(
    body: ResetPasswordRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    user_query = await db.execute(select(User).where(User.email == body.email))
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
    return {"ok": True}

@router.post("/complete-reset", status_code=200)
async def complete_reset(
    body: CompleteResetRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    email = "from_context"
    hashed_token = hash_token(body.token)
    stored = await redis.get(f"reset:{email}")
    if not stored or stored.decode() != hashed_token:
        raise HTTPException(status_code=403, detail="Invalid token")
    await redis.delete(f"reset:{email}")

    pw_hash = hash_password(body.new_password)

    user_query = await db.execute(select(User).where(User.email == email))
    user = user_query.scalar_one_or_none()
    user.password_hash = pw_hash
    await db.commit()

    event = {"event": "user.password_reset", "user_id": str(user.id)}
    await send_event("budget.auth.events", event, AUTH_EVENTS_SCHEMA)
    return {"ok": True}

@router.post("/change-password", status_code=200)
async def change_password(
    body: ChangePasswordRequest = Body(...),
    db: AsyncSession = Depends(get_db)
):
    user_query = await db.execute(select(User).where(User.id == body.user_id))
    user = user_query.scalar_one_or_none()
    if not user or not check_password(body.password, user.password_hash):
        raise HTTPException(status_code=403, detail="Invalid current password")

    pw_hash = hash_password(body.new_password)
    user.password_hash = pw_hash
    await db.commit()

    event = {"event": "user.password_changed", "user_id": str(body.user_id)}
    await send_event("budget.auth.events", event, AUTH_EVENTS_SCHEMA)
    return {"ok": True}

@router.post("/validate-token", status_code=200)
async def validate_token(
    body: TokenValidateRequest = Body(...),
):
    try:
        payload = decode(body.token, settings.jwt_secret, algorithms=["HS256"])
        if "sub" not in payload:
            raise PyJWTError("Missing sub")
        return {"ok": True}
    except PyJWTError:
        event = {"event": "user.token_invalid", "token": "anonymized"}
        await send_event("budget.auth.events", event, AUTH_EVENTS_SCHEMA)
        raise HTTPException(status_code=401, detail="Invalid token")

@router.post("/refresh", status_code=200)
async def refresh(
    body: RefreshRequest = Body(...),
    db: AsyncSession = Depends(get_db)
):
    user_id = "from_context"
    fingerprint = sha256(body.refresh_token.encode()).hexdigest()
    session_query = await db.execute(select(Session).where(
        Session.user_id == user_id,
        Session.refresh_fingerprint == fingerprint,
        Session.revoked == False,
        Session.expires_at > datetime.utcnow()
    ))
    session = session_query.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=403, detail="Invalid refresh token")

    access_payload = {"sub": str(user_id), "exp": datetime.utcnow() + timedelta(minutes=15)}
    access_token = encode(access_payload, settings.jwt_secret, algorithm="HS256")

    response = JSONResponse({"ok": True})
    response.set_cookie("access_token", access_token, httponly=True, secure=True, samesite='strict', max_age=900)
    return response

@router.get("/.well-known/jwks.json")
async def jwks():
    jwks = {
        "keys": [
            {
                "kty": "oct",
                "use": "sig",
                "kid": "sig-1",
                "k": settings.jwt_secret,  # В реальности base64 или public key
                "alg": "HS256"
            }
        ]
    }
    return jwks