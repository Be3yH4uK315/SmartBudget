import pytest
from app.main import app
from asgi_lifespan import LifespanManager

@pytest.mark.asyncio
async def test_lifespan_startup_shutdown():
    async with LifespanManager(app) as manager:
        assert hasattr(app.state, "redis_pool"), "Redis pool initialized on startup"
        assert hasattr(app.state, "arq_pool"), "Arq pool initialized on startup"
        assert app.state.redis_pool is not None
        assert app.state.arq_pool is not None

    assert not hasattr(app.state, "redis_pool")
    assert not hasattr(app.state, "arq_pool")
