import pytest
from app.services import AuthService
from app.schemas import CompleteRegistrationRequest, LoginRequest, ResetPasswordRequest, CompleteResetRequest, ChangePasswordRequest
from uuid import uuid4
from app.utils import hash_token, hash_password, check_password
from unittest.mock import ANY, AsyncMock, patch
from fastapi import HTTPException
from app.models import User, Session, UserRole
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta
from jwt import decode, encode
from app.settings import settings
from redis.asyncio import Redis

@pytest.mark.asyncio
async def test_start_email_verification_new_email(db_session: AsyncSession, test_redis: Redis, mock_arq_pool: AsyncMock):
    service = AuthService(db=db_session, redis=test_redis, arq_pool=mock_arq_pool)
    await service.start_email_verification("new@example.com")
    stored = await test_redis.get("verify:new@example.com")
    assert stored is not None, "Токен должен сохраняться в Redis"
    assert len(stored) == 64, "Хэш sha256"
    mock_arq_pool.enqueue_job.assert_called_once_with('send_email_async', to="new@example.com", subject=ANY, body=ANY)

@pytest.mark.asyncio
async def test_start_email_verification_existing_email(db_session: AsyncSession, test_redis: Redis, mock_arq_pool: AsyncMock):
    user = User(id=uuid4(), email="existing@example.com", password_hash="hash", name="User", country="US", role=UserRole.USER)
    db_session.add(user)
    await db_session.commit()
    service = AuthService(db=db_session, redis=test_redis, arq_pool=mock_arq_pool)
    with pytest.raises(HTTPException) as exc:
        await service.start_email_verification("existing@example.com")
    assert exc.value.status_code == 409, "Конфликт для existing email"
    mock_arq_pool.enqueue_job.assert_not_called()

@pytest.mark.asyncio
async def test_validate_verification_token_valid(test_redis: Redis):
    token = "valid_token"
    hashed = hash_token(token)
    await test_redis.set("verify:test@example.com", hashed, ex=900)
    service = AuthService(db=None, redis=test_redis, arq_pool=None)
    await service.validate_verification_token(token, "test@example.com")

@pytest.mark.asyncio
async def test_validate_verification_token_invalid(test_redis: Redis):
    await test_redis.set("verify:test@example.com", hash_token("wrong"))
    service = AuthService(db=None, redis=test_redis, arq_pool=None)
    with pytest.raises(HTTPException) as exc:
        await service.validate_verification_token("invalid_token", "test@example.com")
    assert exc.value.status_code == 403

@pytest.mark.asyncio
async def test_validate_verification_token_expired(test_redis: Redis):
    service = AuthService(db=None, redis=test_redis, arq_pool=None)
    with pytest.raises(HTTPException) as exc:
        await service.validate_verification_token("token", "no_key@example.com")
    assert exc.value.status_code == 403

@pytest.mark.asyncio
@patch("app.services.get_location", return_value="Test Location")
@patch("app.services.parse_device", return_value="Test Device")
async def test_complete_registration_valid(mock_parse, mock_loc, db_session: AsyncSession, test_redis: Redis, mock_arq_pool: AsyncMock, freeze_utc_now):
    token = "reg_token"
    hashed = hash_token(token)
    await test_redis.set("verify:test@example.com", hashed)
    body = CompleteRegistrationRequest(
        email="test@example.com", name="Test User", country="US", token=token, password="secure123", user_agent="UA"
    )
    service = AuthService(db=db_session, redis=test_redis, arq_pool=mock_arq_pool)
    user, session, access_token, refresh_token = await service.complete_registration(body, ip="127.0.0.1")
    assert user.email == "test@example.com", "User email должен совпадать"
    assert check_password("secure123", user.password_hash), "Пароль должен быть правильно хэширован"
    assert session.device_name == "Test Device", "Device name из parse_device"
    assert session.location == "Test Location", "Location из get_location"
    assert await test_redis.get("verify:test@example.com") is None, "Redis key должен быть удален после верификации"
    
    assert mock_arq_pool.enqueue_job.call_count == 2
    
    expected_event_data = {
        "event": "user.registered", 
        "user_id": str(user.id),
        "email": user.email,
        "ip": "127.0.0.1",
        "location": "Test Location"
    }
    
    expected_user_event = {
        "user_id": str(user.id),
        "email": user.email,
        "name": user.name,
        "country": user.country,
        "role": user.role,
        "is_active": user.is_active
    }
    
    mock_arq_pool.enqueue_job.assert_any_call(
        'send_kafka_event_async', 
        "budget.auth.events",
        expected_event_data,
        "AUTH_EVENTS_SCHEMA"
    )
    
    mock_arq_pool.enqueue_job.assert_any_call(
        'send_kafka_event_async', 
        "users.active",
        expected_user_event,
        "USERS_ACTIVE_SCHEMA"
    )
    
    payload = decode(access_token, settings.jwt_public_key, algorithms=[settings.jwt_algorithm])
    assert payload["sub"] == str(user.id), "JWT sub должен быть user.id"
    assert "exp" in payload, "Должен быть expiration"
    assert payload["role"] == 0, "Role по умолчанию USER"

@pytest.mark.asyncio
async def test_complete_registration_invalid_token(db_session: AsyncSession, test_redis: Redis, mock_arq_pool: AsyncMock):
    body = CompleteRegistrationRequest(email="test@example.com", name="User", country="US", token="wrong", password="password123", user_agent="UA")
    service = AuthService(db=db_session, redis=test_redis, arq_pool=mock_arq_pool)
    with pytest.raises(HTTPException) as exc:
        await service.complete_registration(body, "ip")
    assert exc.value.status_code == 403

