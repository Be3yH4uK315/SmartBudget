from typing import Self
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app import repositories

class UnitOfWork:
    """
    Паттерн Unit of Work. 
    Обеспечивает атомарность операций и инкапсулирует работу с транзакциями.
    """
    
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory
        self._session: AsyncSession | None = None
        self._goal_repo: repositories.GoalRepository | None = None

    async def __aenter__(self) -> Self:
        self._session = self.session_factory()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if not self._session:
            return
            
        try:
            if exc_type:
                await self._session.rollback()
            else:
                await self._session.commit()
        finally:
            await self._session.close()

    @property
    def goal_repository(self) -> repositories.GoalRepository:
        """Инициализация репозитория."""
        if self._session is None:
            raise RuntimeError("UnitOfWork context has not been entered")
            
        if self._goal_repo is None:
            self._goal_repo = repositories.GoalRepository(self._session)
        return self._goal_repo

    async def commit(self):
        """Явный коммит."""
        if self._session:
            await self._session.commit()

    async def rollback(self):
        """Явный откат."""
        if self._session:
            await self._session.rollback()