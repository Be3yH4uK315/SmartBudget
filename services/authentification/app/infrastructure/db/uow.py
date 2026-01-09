from typing import Self
from app.infrastructure.db import repositories

class UnitOfWork:
    """
    Паттерн Unit of Work.
    Управляет жизненным циклом сессии и транзакцией.
    """

    def __init__(self, session_factory):
        self.session_factory = session_factory
        self._session = None
        self._repositories: dict[type, object] = {}

    async def __aenter__(self) -> Self:
        self._session = self.session_factory()
        self._repositories = {}
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
    def session(self):
        """Возвращает текущую сессию SQLAlchemy."""
        if self._session is None:
             raise RuntimeError("UoW not started. Use 'async with uow: ...'")
        return self._session
    
    async def commit(self) -> None:
        """Ручной коммит транзакции."""
        if self._session is None:
            raise RuntimeError("UoW not started")
        await self._session.commit()

    async def rollback(self) -> None:
        """Ручной откат транзакции."""
        if self._session is None:
            raise RuntimeError("UoW not started")
        await self._session.rollback()
    
    async def flush(self) -> None:
        if self._session is None:
            raise RuntimeError("UoW not started")
        await self._session.flush()

    def _get_repository(self, repo_cls):
        """Инициализация репозитория."""
        if self._session is None:
            raise RuntimeError("UoW not started")

        if repo_cls not in self._repositories:
            self._repositories[repo_cls] = repo_cls(self._session)
        return self._repositories[repo_cls]

    @property
    def users(self) -> repositories.UserRepository:
        return self._get_repository(repositories.UserRepository)

    @property
    def sessions(self) -> repositories.SessionRepository:
        return self._get_repository(repositories.SessionRepository)
