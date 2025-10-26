import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_verify_email():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/verify-email", json={"email": "test@example.com"})
        assert response.status_code == 200
        assert response.json() == {"ok": True}