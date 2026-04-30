from typing import Self
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.infrastructure.db.repositories import (
    rules, ml, classification, outbox
)

class UnitOfWork:
    """
    Паттерн Unit of Work. Инкапсулирует работу с транзакциями.
    """
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory
        self._session: AsyncSession | None = None

        self._categories = None
        self._rules = None
        self._results = None
        self._feedback = None
        self._models = None
        self._datasets = None
        self._outbox = None

    async def __aenter__(self) -> Self:
        self._session = self.session_factory()
        self._reset_repositories()
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
            self._session = None
            self._reset_repositories()
    
    async def commit(self):
        """Фиксирует текущую транзакцию."""
        if self._session:
            await self._session.commit()

    async def rollback(self):
        """Откатывает текущую транзакцию."""
        if self._session:
            await self._session.rollback()

    async def close(self):
        """Закрывает сессию."""
        if self._session:
            await self._session.close()
    
    def make_savepoint(self):
        """Создает вложенную транзакцию (SAVEPOINT)."""
        if not self._session:
            raise RuntimeError("Session is not active. Use 'async with uow:' first.")
        return self._session.begin_nested()

    def _ensure_session(self) -> AsyncSession:
        if self._session is None:
            raise RuntimeError("UoW not started. Use 'async with uow: ...'")
        return self._session

    def _reset_repositories(self) -> None:
        self._categories = None
        self._rules = None
        self._results = None
        self._feedback = None
        self._models = None
        self._datasets = None
        self._outbox = None

    @property
    def categories(self) -> rules.CategoryRepository:
        if not self._categories:
            self._categories = rules.CategoryRepository(self._ensure_session())
        return self._categories
    
    @property
    def rules(self) -> rules.RuleRepository:
        if not self._rules:
            self._rules = rules.RuleRepository(self._ensure_session())
        return self._rules

    @property
    def results(self) -> classification.ClassificationResultRepository:
        if not self._results:
            self._results = classification.ClassificationResultRepository(self._ensure_session())
        return self._results

    @property
    def feedback(self) -> classification.FeedbackRepository:
        if not self._feedback:
            self._feedback = classification.FeedbackRepository(self._ensure_session())
        return self._feedback
    
    @property
    def models(self) -> ml.ModelRepository:
        if not self._models:
            self._models = ml.ModelRepository(self._ensure_session())
        return self._models

    @property
    def datasets(self) -> ml.DatasetRepository:
        if not self._datasets:
            self._datasets = ml.DatasetRepository(self._ensure_session())
        return self._datasets

    @property
    def outbox(self) -> outbox.OutboxRepository:
        if not self._outbox:
            self._outbox = outbox.OutboxRepository(self._ensure_session())
        return self._outbox
