from sqlalchemy.ext.asyncio import AsyncSession


class BaseRepository:
    """Базовый класс репозиториев."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
