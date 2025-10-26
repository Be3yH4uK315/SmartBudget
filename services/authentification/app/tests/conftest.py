import pytest
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.db import Base
from app.settings import settings
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import timezone
import sqlalchemy as sa
from uuid import uuid4

@pytest.fixture(scope="module")
def test_engine():
    return create_async_engine(settings.db_url.replace("/auth_db", "/test_auth_db"))

@pytest.fixture(scope="function")
async def test_db(test_engine):
    async_session = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_session() as session:
        yield session
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
def mock_redis():
    mock = MagicMock(spec=Redis)
    mock.get = AsyncMock()
    mock.set = AsyncMock()
    mock.delete = AsyncMock()
    mock.incr = AsyncMock(return_value=1)
    mock.expire = AsyncMock()
    with patch('app.dependencies.Redis.from_url', return_value=mock):
        yield mock

@pytest.fixture
def mock_kafka():
    mock_producer = MagicMock()
    mock_producer.send_and_wait = AsyncMock()
    with patch('app.kafka.producer', mock_producer):
        yield mock_producer

@pytest.fixture
def mock_celery():
    with patch('app.tasks.send_email_wrapper.delay') as mock:
        yield mock

@pytest.fixture
def mock_geoip():
    with patch('app.utils.geoip2.database.Reader') as mock_reader:
        mock_geo = MagicMock()
        mock_geo.country.name = "Test Country"
        mock_geo.city.name = "Test City"
        mock_reader.return_value.city.return_value = mock_geo
        yield mock_reader

@pytest.fixture
def mock_settings():
    with patch('app.settings.settings') as mock:
        mock.env = 'dev'
        mock.jwt_secret = 'test_secret'
        yield mock