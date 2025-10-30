import pytest
from httpx import AsyncClient
from app.middleware import logger as middleware_logger
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from jwt.exceptions import PyJWTError
from aiokafka.errors import KafkaError
from unittest.mock import ANY, patch, AsyncMock

pytestmark = pytest.mark.asyncio

@patch("app.services.AuthService.start_email_verification", new_callable=AsyncMock)
async def test_error_middleware_integrity(mock_service_call: AsyncMock, client: AsyncClient, caplog):
    mock_service_call.side_effect = IntegrityError("param", "params", "orig")
    response = await client.post("/verify-email", json={"email": "test@example.com"})
    
    assert response.status_code == 409, "Status для IntegrityError"
    assert response.json() == {"detail": "Duplicate entry"}, "JSON response"
    
    assert "Integrity error" in caplog.text
    assert "ERROR" in caplog.text

@patch("app.services.AuthService.start_email_verification", new_callable=AsyncMock)
async def test_error_middleware_sqlalchemy(mock_service_call: AsyncMock, client: AsyncClient, caplog):
    mock_service_call.side_effect = SQLAlchemyError("db error")
    
    response = await client.post("/verify-email", json={"email": "test@example.com"})
    
    assert response.status_code == 500
    assert response.json() == {"detail": "Database error"}
    assert "Database error" in caplog.text

@patch("app.dependencies.get_real_ip", new_callable=AsyncMock, side_effect=PyJWTError("jwt error"))
async def test_error_middleware_pyjwt(mock_get_ip: AsyncMock, client: AsyncClient, caplog):
    response = await client.post("/login", json={"email": "a@b.com", "password": "123", "user_agent": "ua"})
    
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid token"}
    assert "JWT error" in caplog.text

@patch("app.dependencies.get_real_ip", new_callable=AsyncMock, side_effect=KafkaError("kafka error"))
async def test_error_middleware_kafka(mock_get_ip: AsyncMock, client: AsyncClient, caplog):
    response = await client.post("/login", json={"email": "a@b.com", "password": "123", "user_agent": "ua"})
    
    assert response.status_code == 500
    assert response.json() == {"detail": "Kafka error"}
    assert "Kafka error" in caplog.text

@patch("app.dependencies.get_real_ip", new_callable=AsyncMock, side_effect=Exception("unexpected"))
async def test_error_middleware_generic(mock_get_ip: AsyncMock, client: AsyncClient, caplog):
    response = await client.post("/login", json={"email": "a@b.com", "password": "123", "user_agent": "ua"})
    
    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}
    assert "Unexpected error" in caplog.text

