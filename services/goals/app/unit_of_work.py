from typing import Self

from app import repositories

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

    def _get_repository(self, repo_cls):
        """Инициализация репозитория."""
        if self._session is None:
            raise RuntimeError("UoW not started")
        
        if repo_cls not in self._repositories:
            self._repositories[repo_cls] = repo_cls(self._session)
        return self._repositories[repo_cls]

    @property
    def goals(self) -> repositories.GoalRepository:
        """Удобный алиас, но внутри используется generic механизм."""
        return self._get_repository(repositories.GoalRepository)