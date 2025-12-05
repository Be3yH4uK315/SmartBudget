import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from asgi_lifespan import LifespanManager
from unittest.mock import AsyncMock
from redis.asyncio import Redis
from faker import Faker
from datetime import datetime, timezone
from freezegun import freeze_time

from app.main import app
from app.settings import settings
from app.dependencies import get_db, get_redis, get_arq_pool
from app.models import Base

test_engine = create_async_engine(settings.db_url, poolclass=NullPool)
TestSessionLocal = async_sessionmaker(
    test_engine, 
    class_=AsyncSession,
    expire_on_commit=False
)

@pytest_asyncio.fixture(scope="function")
async def db_session():
    """
    Фикстура для сессии БД.
    Очищает и создает заново все таблицы перед каждым тестом.
    """
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()
    
    await session.close()

@pytest_asyncio.fixture(scope="function")
async def test_redis():
    """
    Фикстура для клиента Redis, подключенного к *тестовой*
    базе Redis (auth_redis_test:6379).
    """
    client = Redis.from_url(settings.redis_url, decode_responses=True)
    await client.flushdb()
    yield client
    await client.flushdb()
    await client.aclose()

@pytest_asyncio.fixture(scope="function")
async def mock_arq_pool():
    """ "Мок" для пула Arq, чтобы не слать email/kafka. """
    pool = AsyncMock(spec=AsyncMock)
    pool.enqueue_job = AsyncMock()
    yield pool

@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession, test_redis: Redis, mock_arq_pool: AsyncMock):
    """
    Главная фикстура, использующая httpx.AsyncClient.
    """
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_redis] = lambda: test_redis
    app.dependency_overrides[get_arq_pool] = lambda: mock_arq_pool
    transport = ASGITransport(app=app)
    async with LifespanManager(app):
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            c.mock_arq_pool = mock_arq_pool
            yield c
    app.dependency_overrides = {}

@pytest_asyncio.fixture(scope="session")
def faker():
    return Faker()

@pytest_asyncio.fixture
def freeze_utc_now():
    with freeze_time(datetime(2025, 10, 29, tzinfo=timezone.utc)) as frozen:
        yield frozen
