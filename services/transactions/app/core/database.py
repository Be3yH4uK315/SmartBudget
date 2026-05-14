from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings


def get_db_engine() -> AsyncEngine:
    """Создает асинхронный SQLAlchemy engine."""
    return create_async_engine(
        settings.DB.DB_URL,
        pool_size=settings.DB.DB_POOL_SIZE,
        max_overflow=settings.DB.DB_MAX_OVERFLOW,
        echo=False,
        pool_pre_ping=True,
    )


def get_session_factory(
    engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    """Создает фабрику асинхронных SQLAlchemy-сессий."""
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
