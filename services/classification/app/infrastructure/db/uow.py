from contextlib import asynccontextmanager
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.infrastructure.db.repositories import (
    CategoryRepository,
    ClassificationResultRepository,
    DatasetRepository,
    FeedbackRepository,
    ModelRepository,
    OutboxRepository,
    RuleRepository,
)


class UnitOfWork:
    """
    Паттерн Unit of Work.
    Управляет жизненным циклом сессии и транзакцией.
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory
        self._session: AsyncSession | None = None
        self._committed = False
        self._repositories: dict[type, object] = {}

    async def __aenter__(self) -> Self:
        self._session = self.session_factory()
        self._committed = False
        self._repositories = {}
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
    def session(self) -> AsyncSession:
        """Возвращает текущую сессию SQLAlchemy."""
        if self._session is None:
            raise RuntimeError("UoW not started. Use 'async with uow: ...'")
        return self._session

    async def commit(self) -> None:
        """Ручной коммит транзакции."""
        await self.session.commit()
        self._committed = True

    async def rollback(self) -> None:
        """Ручной откат транзакции."""
        await self.session.rollback()

    async def flush(self) -> None:
        if self._session is None:
            raise RuntimeError("UoW not started")
        await self._session.flush()

    async def refresh(
        self,
        instance: object,
        attribute_names: list[str] | None = None,
    ) -> None:
        """Метод для обновления состояния объекта из базы данных."""
        if self._session is None:
            raise RuntimeError("UoW not started")
        await self._session.refresh(instance, attribute_names)

    @asynccontextmanager
    async def make_savepoint(self):
        """Создает точку сохранения (вложенную транзакцию)."""
        async with self.session.begin_nested():
            yield

    def _get_repository(self, repo_cls):
        """Инициализация репозитория."""
        if repo_cls not in self._repositories:
            self._repositories[repo_cls] = repo_cls(self.session)
        return self._repositories[repo_cls]

    @property
    def categories(self) -> CategoryRepository:
        return self._get_repository(CategoryRepository)

    @property
    def rules(self) -> RuleRepository:
        return self._get_repository(RuleRepository)

    @property
    def results(self) -> ClassificationResultRepository:
        return self._get_repository(ClassificationResultRepository)

    @property
    def feedback(self) -> FeedbackRepository:
        return self._get_repository(FeedbackRepository)

    @property
    def models(self) -> ModelRepository:
        return self._get_repository(ModelRepository)

    @property
    def datasets(self) -> DatasetRepository:
        return self._get_repository(DatasetRepository)

    @property
    def outbox(self) -> OutboxRepository:
        return self._get_repository(OutboxRepository)
