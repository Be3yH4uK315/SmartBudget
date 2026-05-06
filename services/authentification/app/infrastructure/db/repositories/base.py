from sqlalchemy.ext.asyncio import AsyncSession

class BaseRepository:
    """Базовый репозиторий."""

    def __init__(self, db: AsyncSession):
        self.db = db
