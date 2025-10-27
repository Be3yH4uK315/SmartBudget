import pytest
from unittest.mock import patch, AsyncMock
from app.kafka import send_event, AUTH_EVENTS_SCHEMA, USERS_ACTIVE_SCHEMA
from app.tasks import send_email_async
from app.utils import get_location, parse_device, hash_token, hash_password, check_password
from uuid import uuid4
from aiosmtplib import SMTPException
from geoip2.errors import AddressNotFoundError

@pytest.mark.asyncio
async def test_send_event_success(mock_kafka):
    event = {
        "event": "user.login",
        "user_id": str(uuid4()),
        "email": "test@example.com",
        "ip": "192.168.1.1",
        "location": "Moscow"
    }
    await send_event("budget.auth.events", event, AUTH_EVENTS_SCHEMA)
    mock_kafka.send_and_wait.assert_called_once()

@pytest.mark.asyncio
async def test_send_event_invalid_schema(mock_kafka):
    invalid_event = {"event": "invalid_event_type", "user_id": str(uuid4())}
    with pytest.raises(ValueError):
        await send_event("budget.auth.events", invalid_event, AUTH_EVENTS_SCHEMA)
    mock_kafka.send_and_wait.assert_not_called()

@pytest.mark.asyncio
async def test_send_event_users_active_schema(mock_kafka):
    event = {
        "user_id": str(uuid4()),
        "email": "test@example.com",
        "name": "Test User",
        "country": "Russia",
        "role": 0,
        "is_active": True
    }
    await send_event("users.active", event, USERS_ACTIVE_SCHEMA)
    mock_kafka.send_and_wait.assert_called_once()

@pytest.mark.asyncio
async def test_send_email_async_success(mock_settings):
    with patch('app.tasks.send') as mock_send:
        mock_send.return_value = AsyncMock()
        await send_email_async("test@example.com", "Test Subject", "Test Body")
        mock_send.assert_called_once()

@pytest.mark.asyncio
async def test_send_email_async_failure(mock_settings):
    with patch('app.tasks.send', side_effect=SMTPException("SMTP error simulation")):
        with pytest.raises(SMTPException):
            await send_email_async("test@example.com", "Test Subject", "Test Body")

@pytest.mark.asyncio
async def test_get_location_success(mock_geoip):
    location = get_location("8.8.8.8")
    assert location == "Test Country, Test City"

@pytest.mark.asyncio
async def test_get_location_failure_no_db():
    with patch('os.path.exists', return_value=False):
        location = get_location("8.8.8.8")
        assert location == "Unknown"

def test_get_location_address_not_found(mock_geoip):
    """Тестирует fallback на 'Unknown' если адрес не найден."""
    # Устанавливаем side_effect на mocked city
    mock_geoip.return_value.city.side_effect = AddressNotFoundError("Not found")
    location = get_location("invalid_ip")
    assert location == "Unknown"

def test_parse_device():
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    device = parse_device(user_agent)
    assert "Other, Windows 10" in device

def test_hash_token():
    token = "sample_token"
    hashed = hash_token(token)
    assert hashed == "1d0b4e324feed3becc6b09386ce245f8c352874b96d906ce883895bf2a3f3546"

def test_hash_password_and_check():
    password = "strongpass123"
    hashed = hash_password(password)
    assert check_password(password, hashed) is True
    assert check_password("wrongpass", hashed) is False