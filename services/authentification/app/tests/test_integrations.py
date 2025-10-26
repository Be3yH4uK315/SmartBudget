from uuid import uuid4
import pytest
from aiosmtplib import SMTPException
from app.kafka import send_event, AUTH_EVENTS_SCHEMA
from app.tasks import send_email_async
from app.utils import get_location
from unittest.mock import patch

@pytest.mark.asyncio
async def test_send_event(mock_kafka):
    event = {"event": "user.login", "user_id": str(uuid4())}
    await send_event("test_topic", event, AUTH_EVENTS_SCHEMA)
    mock_kafka.send_and_wait.assert_called_once()

    invalid_event = {"event": "invalid"}
    with pytest.raises(ValueError):
        await send_event("test", invalid_event, AUTH_EVENTS_SCHEMA)

@pytest.mark.asyncio
async def test_send_email_async(mock_settings):
    with patch('app.tasks.send') as mock_send:
        await send_email_async("test@example.com", "subject", "body")
        mock_send.assert_called_once()

    with patch('app.tasks.send', side_effect=SMTPException("test error")):
        with pytest.raises(SMTPException):
            await send_email_async("test@example.com", "subject", "body")

@pytest.mark.asyncio
async def test_get_location(mock_geoip):
    assert get_location("8.8.8.8") == "Test Country, Test City"

    with patch('os.path.exists', return_value=False):
        assert get_location("8.8.8.8") == "Unknown"