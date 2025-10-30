from fastapi import HTTPException
import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch

pytestmark = pytest.mark.asyncio

async def test_verify_email_valid(client: AsyncClient):
    data = {"email": "verify@example.com"}
    response = await client.post("/verify-email", json=data)
    assert response.status_code == 200, "Успешная верификация start"
    assert response.json() == {"ok": True}, "Status ok"
    mock_arq: AsyncMock = client.mock_arq_pool
    mock_arq.enqueue_job.assert_called_once()

async def test_verify_email_invalid_format(client: AsyncClient):
    data = {"email": "invalid"}
    response = await client.post("/verify-email", json=data)
    assert response.status_code == 422, "Pydantic validation error"
    assert "detail" in response.json()

async def test_verify_link_valid(client: AsyncClient):
    with patch("app.services.AuthService.validate_verification_token", AsyncMock(return_value=None)) as mock_validate:
        response = await client.get("/verify-link?token=valid&email=test@example.com")
        assert response.status_code == 200
        assert response.json() == {"ok": True}
        mock_validate.assert_called_once_with("valid", "test@example.com")

async def test_verify_link_invalid(client: AsyncClient):
    with patch("app.services.AuthService.validate_verification_token", AsyncMock(side_effect=HTTPException(status_code=403))):
        response = await client.get("/verify-link?token=invalid&email=test@example.com")
        assert response.status_code == 403

async def test_complete_registration_valid(client: AsyncClient):
    body = {"email": "reg@example.com", "name": "User", "country": "US", "token": "valid", "password": "secure123", "user_agent": "UA"}
    mock_user = MagicMock(id=MagicMock())
    mock_session = MagicMock()
    with patch("app.services.AuthService.complete_registration", AsyncMock(return_value=(mock_user, mock_session, "access_token_value", "refresh_token_value"))):
        response = await client.post("/complete-registration", json=body)
        assert response.status_code == 200
        assert response.json() == {"ok": True}
        assert "access_token" in response.cookies
        assert "refresh_token" in response.cookies
        assert response.cookies["access_token"] == "access_token_value"
