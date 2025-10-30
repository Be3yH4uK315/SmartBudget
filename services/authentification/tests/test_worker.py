from uuid import uuid4
from aiosmtplib import SMTPException
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.settings import settings
from app.worker import send_email_async, send_kafka_event_async, cleanup_sessions_async
from unittest.mock import ANY, AsyncMock, patch
from app.models import Session, User, UserRole
from datetime import datetime, timezone, timedelta
from jsonschema.exceptions import ValidationError
from aiokafka.errors import KafkaConnectionError
from tests.conftest import TestSessionLocal 

@pytest.mark.asyncio
@patch("app.worker.send")
async def test_send_email_async_valid(mock_send):
    ctx = {}
    await send_email_async(ctx, "to@example.com", "Subject", "Body text")
    mock_send.assert_called_once()
    assert mock_send.call_args.kwargs["hostname"] == settings.smtp_host, "Использует settings"

@pytest.mark.asyncio
@patch("app.worker.send", side_effect=SMTPException("SMTP fail"))
async def test_send_email_async_error(mock_send):
    ctx = {}
    with pytest.raises(SMTPException):
        await send_email_async(ctx, "to@example.com", "Sub", "Body")

@pytest.mark.asyncio
async def test_send_kafka_event_async_valid():
    ctx = {"kafka_producer": AsyncMock()}
    event_data = {"event": "user.registered", "user_id": str(uuid4())}
    await send_kafka_event_async(ctx, "topic", event_data, "AUTH_EVENTS_SCHEMA")
    ctx["kafka_producer"].send_and_wait.assert_called_once_with("topic", value=ANY)

@pytest.mark.asyncio
async def test_send_kafka_event_async_invalid_schema():
    ctx = {"kafka_producer": AsyncMock()}
    invalid_data = {"event": "invalid"}
    with pytest.raises(ValidationError):
        await send_kafka_event_async(ctx, "topic", invalid_data, "AUTH_EVENTS_SCHEMA")
    ctx["kafka_producer"].send_and_wait.assert_not_called()

@pytest.mark.asyncio
async def test_send_kafka_event_async_connection_error():
    producer = AsyncMock()
    producer.send_and_wait.side_effect = KafkaConnectionError("Conn fail")
    ctx = {"kafka_producer": producer}
    data = {"event": "user.login", "user_id": str(uuid4())}
    with pytest.raises(KafkaConnectionError):
        await send_kafka_event_async(ctx, "topic", data, "AUTH_EVENTS_SCHEMA")

@pytest.mark.asyncio
async def test_cleanup_sessions_async_valid(db_session: AsyncSession):
    user = User(
        email="test@example.com",
        password_hash="hash",
        name="Test User",
        country="Localhost",
        is_active=True,
        role=UserRole.USER
    )
    db_session.add(user)
    await db_session.flush()

    expired_session = Session(id=uuid4(), user_id=user.id, expires_at=datetime.now(timezone.utc) - timedelta(days=1), revoked=False, user_agent="test", device_name="test", ip="127.0.0.1", location="Local", refresh_fingerprint="fp1")
    revoked_session = Session(id=uuid4(), user_id=user.id, expires_at=datetime.now(timezone.utc) + timedelta(days=1), revoked=True, user_agent="test", device_name="test", ip="127.0.0.1", location="Local", refresh_fingerprint="fp2")
    active_session = Session(id=uuid4(), user_id=user.id, expires_at=datetime.now(timezone.utc) + timedelta(days=1), revoked=False, user_agent="test", device_name="test", ip="127.0.0.1", location="Local", refresh_fingerprint="fp3")

    db_session.add_all([expired_session, revoked_session, active_session])
    await db_session.commit()

    mock_maker = AsyncMock(return_value=db_session)
    async def mock_session_context(*args, **kwargs):
        yield db_session
    
    mock_maker = mock_session_context
    mock_ctx = {"db_session_maker": TestSessionLocal}
    await cleanup_sessions_async(mock_ctx)
    
    result = await db_session.execute(select(Session))
    sessions = result.scalars().all()
    assert len(sessions) == 1
    assert sessions[0].id == active_session.id


@pytest.mark.asyncio
async def test_cleanup_sessions_async_error(db_session: AsyncSession):
    with patch.object(AsyncSession, 'execute', side_effect=Exception("DB error")):
        ctx = {"db_session_maker": TestSessionLocal}
        
        with pytest.raises(Exception, match="DB error"):
            await cleanup_sessions_async(ctx)

