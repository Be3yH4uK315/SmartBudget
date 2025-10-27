import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from unittest.mock import MagicMock, AsyncMock, patch
from httpx import AsyncClient, ASGITransport  # Добавлен ASGITransport
from redis.asyncio import Redis
from app.main import app as main_app
from app.db import Base, get_db
from app.dependencies import get_redis
from app.settings import settings
from fastapi_limiter import FastAPILimiter  # Для mock init
from app.kafka import producer, startup_kafka, shutdown_kafka  # Для mock

# Фикстура приложения
@pytest.fixture(scope="session")
def app():
    yield main_app

# Фикстура тестового движка БД
@pytest.fixture(scope="module")
def test_engine():
    test_db_url = "sqlite+aiosqlite:///:memory:"
    engine = create_async_engine(test_db_url, echo=False)
    yield engine

# Фикстура асинхронной сессии БД
@pytest_asyncio.fixture(scope="function")
async def test_db(test_engine) -> AsyncSession:
    async_session = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session() as session:
        yield session
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

# Mock для Redis
@pytest.fixture(scope="function")
def mock_redis():
    mock = MagicMock(spec=Redis)
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock()
    mock.delete = AsyncMock()
    mock.incr = AsyncMock(return_value=1)
    mock.expire = AsyncMock()
    yield mock

# Mock для Kafka producer и startup/shutdown
@pytest.fixture(scope="function")
def mock_kafka():
    mock_producer = MagicMock()
    mock_producer.start = AsyncMock()
    mock_producer.stop = AsyncMock()
    mock_producer.send_and_wait = AsyncMock()
    with patch('app.kafka.producer', mock_producer), \
         patch('app.kafka.startup_kafka', AsyncMock()), \
         patch('app.kafka.shutdown_kafka', AsyncMock()):
        yield mock_producer

# Mock для Celery
@pytest.fixture(scope="function")
def mock_celery():
    with patch('app.tasks.send_email_wrapper.delay') as mock_delay:
        yield mock_delay

# Mock для GeoIP
@pytest.fixture(scope="function")
def mock_geoip():
    with patch('app.utils.geoip2.database.Reader') as mock_reader:
        mock_geo = MagicMock()
        mock_geo.country.name = "Test Country"
        mock_geo.city.name = "Test City"
        mock_reader.return_value.city.return_value = mock_geo
        yield mock_reader

# Mock для settings
@pytest.fixture(scope="function")
def mock_settings():
    with patch('app.settings.settings') as mock:
        mock.env = 'dev'
        mock.jwt_secret = 'test_jwt_secret_key_for_testing'
        mock.geoip_db_path = '/fake/path/to/geoip.db'
        mock.smtp_host = 'test.smtp.com'
        mock.smtp_port = 587
        mock.smtp_user = 'test_user'
        mock.smtp_pass = 'test_pass'
        yield mock

# Фикстура API-клиента с overrides и init limiter/Kafka
@pytest_asyncio.fixture(scope="function")
async def client(app, test_db, mock_redis, mock_settings, mock_kafka):
    # Mock FastAPILimiter init to avoid "must call init" error
    with patch('fastapi_limiter.FastAPILimiter.init', MagicMock()):
        app.dependency_overrides[get_db] = lambda: test_db
        app.dependency_overrides[get_redis] = lambda: mock_redis
        
        # Init Kafka mock
        await startup_kafka()
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:  # Fix deprecation
            yield c
        
        await shutdown_kafka()
        app.dependency_overrides = {}