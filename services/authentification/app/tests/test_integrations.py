import pytest
from unittest.mock import AsyncMock
from app.kafka import send_event

@pytest.mark.asyncio
async def test_send_event(monkeypatch):
    mock_producer = AsyncMock()
    monkeypatch.setattr("app.kafka.producer", mock_producer)
    event = {"event": "test", "user_id": "uuid"}
    await send_event("test_topic", event, {})
    mock_producer.send_and_wait.assert_called_once()