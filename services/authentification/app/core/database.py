from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings

def get_db_engine():
    """Создает Singleton Engine."""
    return create_async_engine(
        settings.DB.DB_URL,
        pool_size=settings.DB.DB_POOL_SIZE,
        max_overflow=settings.DB.DB_MAX_OVERFLOW,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=False,
    )

def get_session_factory(engine):
    """Создает фабрику сессий."""
    return async_sessionmaker(
        engine, 
        class_=AsyncSession, 
        expire_on_commit=False
    )
