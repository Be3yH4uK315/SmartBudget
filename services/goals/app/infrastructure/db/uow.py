from typing import Self

from app.infrastructure.db import repositories

class UnitOfWork:
    """
    Паттерн Unit of Work. 
    Обеспечивает атомарность операций и инкапсулирует работу с транзакциями.
    """
    
    def __init__(self, session_factory):
        self.session_factory = session_factory
        self._session = None
        self._repositories = {}

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
    def goals(self) -> repositories.GoalRepository:
        if self._session is None: raise RuntimeError("UoW not started")
        if repositories.GoalRepository not in self._repositories:
            self._repositories[repositories.GoalRepository] = repositories.GoalRepository(self._session)
        return self._repositories[repositories.GoalRepository]