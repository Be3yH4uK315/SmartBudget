from sqlalchemy.ext.asyncio import AsyncSession


class BaseRepository:
    """Базовый репозиторий."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
