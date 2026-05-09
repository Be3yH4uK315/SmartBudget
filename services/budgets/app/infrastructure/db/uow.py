from contextlib import asynccontextmanager
from typing import Self

from app.infrastructure.db.repositories import BudgetRepository, OutboxRepository


class UnitOfWork:
    """Паттерн Unit of Work."""

    def __init__(self, session_factory):
        self.session_factory = session_factory
        self._session = None
        self._committed = False
        self._repositories: dict[type, object] = {}

    async def __aenter__(self) -> Self:
        self._session = self.session_factory()
        self._repositories = {}
        self._committed = False
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if not self._session:
            return
        try:
            if exc_type:
                await self._session.rollback()
            elif not self._committed:
                await self._session.commit()
        finally:
            await self._session.close()
            self._session = None
            self._repositories = {}

    @property
    def session(self):
        if self._session is None:
            raise RuntimeError("UoW not started. Use 'async with uow: ...'")
        return self._session

    async def commit(self) -> None:
        if self._session is None:
            raise RuntimeError("UoW not started")
        await self._session.commit()
        self._committed = True

    async def rollback(self) -> None:
        if self._session is None:
            raise RuntimeError("UoW not started")
        await self._session.rollback()

    async def refresh(self, instance: object, attribute_names: list[str] | None = None) -> None:
        if self._session is None:
            raise RuntimeError("UoW not started")
        await self._session.refresh(instance, attribute_names)

    async def flush(self) -> None:
        if self._session is None:
            raise RuntimeError("UoW not started")
        await self._session.flush()

    @asynccontextmanager
    async def make_savepoint(self):
        if self._session is None:
            raise RuntimeError("UoW not started")

        async with self._session.begin_nested():
            yield

    def _get_repository(self, repo_cls):
        if self._session is None:
            raise RuntimeError("UoW not started")

        if repo_cls not in self._repositories:
            self._repositories[repo_cls] = repo_cls(self._session)
        return self._repositories[repo_cls]

    @property
    def budgets(self) -> BudgetRepository:
        return self._get_repository(BudgetRepository)

    @property
    def outbox(self) -> OutboxRepository:
        return self._get_repository(OutboxRepository)
