import pytest
import httpx
from fastapi import status
from unittest.mock import ANY
from uuid import uuid4
from datetime import datetime, timedelta, timezone
from jwt import encode
from sqlalchemy import select
from app.models import User, Session
from app.utils import hash_password, hash_token, check_password
from app.settings import settings

@pytest.mark.asyncio
async def test_verify_email_success(client, mock_redis, mock_celery, test_db, mock_settings):
    body = {"email": "new_verify@example.com"}
    response = await client.post("/verify-email", json=body)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"ok": True}
    mock_redis.set.assert_called_once_with(f"verify:{body['email']}", ANY, ex=900)
    mock_celery.assert_called_once_with(
        to=body["email"],
        subject="Verify your email for Budget App",
        body=ANY
    )

@pytest.mark.asyncio
async def test_verify_email_existing_user(client, test_db, mock_settings):
    existing_user = User(
        id=uuid4(),
        role=0,
        email="existing@example.com",
        password_hash=hash_password("password12345"),  # len>=8
        name="Existing",
        country="Russia",
        is_active=True
    )
    test_db.add(existing_user)
    await test_db.commit()

    body = {"email": "existing@example.com"}
    response = await client.post("/verify-email", json=body)
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["detail"] == "Email already registered"

@pytest.mark.asyncio
async def test_verify_link_success(client, mock_redis, mock_settings):
    email = "link@example.com"
    token = "valid_token"
    mock_redis.get.return_value = hash_token(token).encode()
    params = {"token": token, "email": email}
    response = await client.get("/verify-link", params=params)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"ok": True}

@pytest.mark.asyncio
async def test_verify_link_invalid_token(client, mock_redis, mock_settings):
    mock_redis.get.return_value = None
    params = {"token": "invalid", "email": "test@example.com"}
    response = await client.get("/verify-link", params=params)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Invalid or expired token"

@pytest.mark.asyncio
async def test_complete_registration_success(client, mock_redis, mock_kafka, mock_geoip, test_db, mock_settings):
    email = "complete@example.com"
    token = "valid_reg_token"
    mock_redis.get.return_value = hash_token(token).encode()
    body = {
        "email": email,
        "name": "Complete User",
        "country": "Russia",
        "token": token,
        "password": "strongpass12345",  # len>=8
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    response = await client.post("/complete-registration", json=body)
    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies
    mock_redis.delete.assert_called_once_with(f"verify:{email}")
    assert mock_kafka.call_count == 2

    user_query = await test_db.execute(select(User).where(User.email == email))
    user = user_query.scalar_one_or_none()
    assert user is not None
    assert user.name == "Complete User"
    assert user.country == "Russia"
    assert check_password("strongpass12345", user.password_hash)
    assert user.is_active is True

    session_query = await test_db.execute(select(Session).where(Session.user_id == user.id))
    session = session_query.scalar_one_or_none()
    assert session is not None
    assert "Other, Windows 10" in session.device_name
    assert session.location == "Test Country, Test City"

@pytest.mark.asyncio
async def test_complete_registration_invalid_token(client, mock_redis, mock_settings):
    mock_redis.get.return_value = None
    body = {
        "email": "invalid@example.com",
        "name": "Invalid",
        "country": "Russia",
        "token": "invalid_token",
        "password": "password12345",  # len>=8 to avoid 422
        "user_agent": "test"
    }
    response = await client.post("/complete-registration", json=body)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Invalid or expired token"

@pytest.mark.asyncio
async def test_login_success(client, mock_redis, mock_kafka, mock_geoip, test_db, mock_settings):
    user = User(
        id=uuid4(),
        role=0,
        email="login@example.com",
        password_hash=hash_password("loginpass12345"),
        name="Login User",
        country="Russia",
        is_active=True
    )
    test_db.add(user)
    await test_db.commit()

    body = {
        "email": "login@example.com",
        "password": "loginpass12345",
        "user_agent": "Mozilla/5.0"
    }
    response = await client.post("/login", json=body)
    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies
    mock_kafka.assert_called_once()

    await test_db.refresh(user)
    assert user.last_login is not None

@pytest.mark.asyncio
async def test_login_invalid_credentials(client, mock_redis, test_db, mock_settings):
    body = {
        "email": "wrong@example.com",
        "password": "wrongpass12345",
        "user_agent": "test"
    }
    response = await client.post("/login", json=body)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Invalid email or password"
    mock_redis.incr.assert_called_once_with(ANY)

@pytest.mark.asyncio
async def test_logout_success(client, mock_kafka, test_db, mock_settings):
    user_id = uuid4()
    session = Session(
        id=uuid4(),
        user_id=user_id,
        user_agent="Mozilla/5.0",
        device_name="test",
        ip="127.0.0.1",
        location="test",
        revoked=False,
        refresh_fingerprint="test_fingerprint",
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        created_at=datetime.now(timezone.utc)
    )
    test_db.add(session)
    await test_db.commit()

    body = {"user_id": str(user_id), "user_agent": "Mozilla/5.0"}
    response = await client.post("/logout", json=body)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"ok": True}
    mock_kafka.assert_called_once()

    await test_db.refresh(session)
    assert session.revoked is True

@pytest.mark.asyncio
async def test_reset_password_success(client, mock_redis, mock_celery, test_db, mock_settings):
    user = User(
        id=uuid4(),
        role=0,
        email="reset@example.com",
        password_hash=hash_password("oldpass12345"),
        name="Reset User",
        country="Russia",
        is_active=True
    )
    test_db.add(user)
    await test_db.commit()

    body = {"email": "reset@example.com"}
    response = await client.post("/reset-password", json=body)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"ok": True}
    mock_redis.set.assert_called_once_with(ANY, ANY, ex=900)
    mock_celery.assert_called_once()

@pytest.mark.asyncio
async def test_complete_reset_success(client, mock_redis, mock_kafka, test_db, mock_settings):
    email = "complete_reset@example.com"
    token = "valid_reset_token"
    mock_redis.get.return_value = hash_token(token).encode()
    user = User(
        id=uuid4(),
        role=0,
        email=email,
        password_hash=hash_password("oldpass12345"),
        name="Reset",
        country="Russia",
        is_active=True
    )
    test_db.add(user)
    await test_db.commit()

    body = {
        "email": email,
        "token": token,
        "new_password": "newstrongpass12345"
    }
    response = await client.post("/complete-reset", json=body)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"ok": True}
    mock_redis.delete.assert_called_once()
    mock_kafka.assert_called_once()

    await test_db.refresh(user)
    assert check_password("newstrongpass12345", user.password_hash)

@pytest.mark.asyncio
async def test_change_password_success(client, mock_kafka, test_db, mock_settings):
    user_id = uuid4()
    user = User(
        id=user_id,
        role=0,
        email="change@example.com",
        password_hash=hash_password("currentpass12345"),
        name="Change",
        country="Russia",
        is_active=True
    )
    test_db.add(user)
    await test_db.commit()

    body = {
        "user_id": str(user_id),
        "password": "currentpass12345",
        "new_password": "newpass456789"
    }
    response = await client.post("/change-password", json=body)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"ok": True}
    mock_kafka.assert_called_once()

    await test_db.refresh(user)
    assert check_password("newpass456789", user.password_hash)

@pytest.mark.asyncio
async def test_change_password_invalid_current(client, test_db, mock_settings):
    user_id = uuid4()
    user = User(
        id=user_id,
        role=0,
        email="invalid_change@example.com",
        password_hash=hash_password("realpass12345"),
        name="Invalid",
        country="Russia",
        is_active=True
    )
    test_db.add(user)
    await test_db.commit()

    body = {
        "user_id": str(user_id),
        "password": "wrongpass12345",
        "new_password": "newpass456789"
    }
    response = await client.post("/change-password", json=body)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Invalid current password"

@pytest.mark.asyncio
async def test_validate_token_success(client, mock_settings):
    payload = {"sub": str(uuid4()), "exp": datetime.now(timezone.utc) + timedelta(minutes=15)}
    valid_token = encode(payload, mock_settings.jwt_secret, algorithm="HS256")
    body = {"token": valid_token}
    response = await client.post("/validate-token", json=body)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"ok": True}

@pytest.mark.asyncio
async def test_validate_token_invalid(client, mock_kafka, mock_settings):
    body = {"token": "invalid_token"}
    response = await client.post("/validate-token", json=body)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Invalid token"
    mock_kafka.assert_called_once()

@pytest.mark.asyncio
async def test_refresh_success(client, test_db, mock_settings):
    user_id = uuid4()
    # Добавляем User для role query
    user = User(
        id=user_id,
        role=0,
        email="refresh@example.com",
        password_hash=hash_password("pass"),
        name="Refresh",
        country="Russia",
        is_active=True
    )
    test_db.add(user)
    await test_db.commit()

    refresh_token = "valid_refresh_token"
    fingerprint = hash_token(refresh_token)
    session = Session(
        id=uuid4(),
        user_id=user_id,
        user_agent="test",
        device_name="test",
        ip="127.0.0.1",
        location="test",
        revoked=False,
        refresh_fingerprint=fingerprint,
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        created_at=datetime.now(timezone.utc)
    )
    test_db.add(session)
    await test_db.commit()

    expired_payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
        "role": 0
    }
    expired_token = encode(expired_payload, mock_settings.jwt_secret, algorithm="HS256")

    client.cookies = httpx.Cookies({"access_token": expired_token})  # Правильный setup cookies
    body = {"refresh_token": refresh_token}
    response = await client.post("/refresh", json=body)
    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.cookies

@pytest.mark.asyncio
async def test_refresh_invalid_fingerprint(client, test_db, mock_settings):
    user_id = uuid4()
    # Добавляем User
    user = User(
        id=user_id,
        role=0,
        email="invalid_refresh@example.com",
        password_hash=hash_password("pass"),
        name="Invalid Refresh",
        country="Russia",
        is_active=True
    )
    test_db.add(user)
    await test_db.commit()

    session = Session(
        id=uuid4(),
        user_id=user_id,
        user_agent="test",
        device_name="test",
        ip="127.0.0.1",
        location="test",
        revoked=False,
        refresh_fingerprint="wrong_fingerprint",
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        created_at=datetime.now(timezone.utc)
    )
    test_db.add(session)
    await test_db.commit()

    expired_token = encode({"sub": str(user_id)}, mock_settings.jwt_secret, algorithm="HS256")
    client.cookies = httpx.Cookies({"access_token": expired_token})
    body = {"refresh_token": "wrong_refresh"}
    response = await client.post("/refresh", json=body)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Invalid refresh token"

@pytest.mark.asyncio
async def test_get_jwks(client, mock_settings):
    response = await client.get("/.well-known/jwks.json")
    assert response.status_code == status.HTTP_200_OK
    jwks = response.json()
    assert "keys" in jwks
    assert len(jwks["keys"]) == 1
    assert jwks["keys"][0]["alg"] == "HS256"
    assert jwks["keys"][0]["k"] is not None