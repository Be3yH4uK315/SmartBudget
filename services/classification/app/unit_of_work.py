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

        self._categories = None
        self._rules = None
        self._results = None
        self._feedback = None
        self._models = None
        self._datasets = None
        self._outbox = None

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
    def categories(self) -> repositories.CategoryRepository:
        if not self._categories: self._categories = repositories.CategoryRepository(self._session)
        return self._categories
    
    @property
    def rules(self) -> repositories.RuleRepository:
        if not self._rules: self._rules = repositories.RuleRepository(self._session)
        return self._rules

    @property
    def results(self) -> repositories.ClassificationResultRepository:
        if not self._results: self._results = repositories.ClassificationResultRepository(self._session)
        return self._results

    @property
    def feedback(self) -> repositories.FeedbackRepository:
        if not self._feedback: self._feedback = repositories.FeedbackRepository(self._session)
        return self._feedback
    
    @property
    def models(self) -> repositories.ModelRepository:
        if not self._models: self._models = repositories.ModelRepository(self._session)
        return self._models

    @property
    def datasets(self) -> repositories.DatasetRepository:
        if not self._datasets: self._datasets = repositories.DatasetRepository(self._session)
        return self._datasets

    @property
    def outbox(self) -> repositories.OutboxRepository:
        if not self._outbox: self._outbox = repositories.OutboxRepository(self._session)
        return self._outbox