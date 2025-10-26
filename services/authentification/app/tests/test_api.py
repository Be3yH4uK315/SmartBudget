from base64 import encode
import pytest
from httpx import AsyncClient
from app.main import app
from app.models import User, Session
from app.utils import hash_password, hash_token, sha256, check_password
from uuid import uuid4
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
import sqlalchemy as sa
from fastapi import status

@pytest.mark.asyncio
async def test_verify_email(mock_redis, mock_celery, test_db, mock_settings):
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/verify-email", json={"email": "new@example.com"})
        assert response.status_code == 200
        assert response.json() == {"ok": True}
        mock_redis.set.assert_called_once_with("verify:new@example.com", hash_token.call_args[0][0], ex=900)
        mock_celery.assert_called_once()

    user = User(id=uuid4(), role=0, email="existing@example.com", password_hash="hash", name="Test", country="RU", is_active=True)
    test_db.add(user)
    await test_db.commit()
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/verify-email", json={"email": "existing@example.com"})
        assert response.status_code == 409
        assert "detail" in response.json()

@pytest.mark.asyncio
async def test_complete_registration(mock_redis, mock_kafka, mock_geoip, test_db, mock_settings):
    mock_redis.get.return_value = hash_token("valid_token").encode()
    body = {
        "email": "reg@example.com",
        "name": "Reg User",
        "country": "RU",
        "token": "valid_token",
        "password": "strongpass123",
        "user_agent": "Mozilla/5.0"
    }
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/complete-registration", json=body)
        assert response.status_code == 200
        assert "access_token" in response.cookies
        assert "refresh_token" in response.cookies
        mock_redis.delete.assert_called_once_with("verify:reg@example.com")
        mock_kafka.send_and_wait.assert_called()
        assert mock_kafka.send_and_wait.call_count == 2

    user_query = await test_db.execute(select(User).where(User.email == "reg@example.com"))
    user = user_query.scalar_one()
    assert user.role == 0
    assert user.is_active is True
    assert check_password("strongpass123", user.password_hash)

    mock_redis.get.return_value = None
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/complete-registration", json=body)
        assert response.status_code == 403

@pytest.mark.asyncio
async def test_login(mock_redis, mock_kafka, mock_geoip, test_db, mock_settings):
    user = User(id=uuid4(), role=0, email="login@example.com", password_hash=hash_password("pass123"), name="Login", country="RU", is_active=True)
    test_db.add(user)
    await test_db.commit()

    body = {"email": "login@example.com", "password": "pass123", "user_agent": "Mozilla/5.0"}
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/login", json=body)
        assert response.status_code == 200
        mock_kafka.send_and_wait.assert_called_once()

    body["password"] = "wrong"
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/login", json=body)
        assert response.status_code == 403
        mock_redis.incr.assert_called_once()

    mock_redis.get.return_value = b'5'
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/login", json=body)
        assert response.status_code == 429

@pytest.mark.asyncio
async def test_refresh(mock_kafka, test_db, mock_settings):
    user_id = uuid4()
    refresh_token = str(uuid4())
    fingerprint = sha256(refresh_token.encode()).hexdigest()
    session = Session(id=uuid4(), user_id=user_id, user_agent="test", device_name="test", ip="127.0.0.1", location="test", revoked=False, refresh_fingerprint=fingerprint, expires_at=datetime.now(timezone.utc) + timedelta(days=1), created_at=datetime.now(timezone.utc))
    test_db.add(session)
    await test_db.commit()

    expired_access = encode({"sub": str(user_id), "role": 0}, mock_settings.jwt_secret, algorithm="HS256")
    body = {"refresh_token": refresh_token}
    async with AsyncClient(app=app, base_url="http://test") as client:
        client.cookies.set("access_token", expired_access)
        response = await client.post("/refresh", json=body)
        assert response.status_code == 200
        assert "access_token" in response.cookies

    body["refresh_token"] = "wrong"
    async with AsyncClient(app=app, base_url="http://test") as client:
        client.cookies.set("access_token", expired_access)
        response = await client.post("/refresh", json=body)
        assert response.status_code == 403
