from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from typing import Self, TypeVar

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

RepositoryType = TypeVar("RepositoryType")


class UnitOfWork:
    """
    Unit of Work.

    Управляет жизненным циклом SQLAlchemy-сессии, транзакцией
    и ленивой инициализацией репозиториев.
    """

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self.session_factory = session_factory
        self._session: AsyncSession | None = None
        self._committed = False
        self._repositories: dict[type, object] = {}

    async def __aenter__(self) -> Self:
        self._session = self.session_factory()
        self._committed = False
        self._repositories = {}

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._session is None:
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
        """Возвращает текущую SQLAlchemy-сессию."""
        if self._session is None:
            raise RuntimeError("UoW not started. Use 'async with uow: ...'")

        return self._session

    async def commit(self) -> None:
        """Выполняет ручной commit транзакции."""
        if self._session is None:
            raise RuntimeError("UoW not started")

        await self._session.commit()
        self._committed = True

    async def rollback(self) -> None:
        """Выполняет ручной rollback транзакции."""
        if self._session is None:
            raise RuntimeError("UoW not started")

        await self._session.rollback()

    async def flush(self) -> None:
        """Отправляет изменения в БД без commit."""
        if self._session is None:
            raise RuntimeError("UoW not started")

        await self._session.flush()

    async def refresh(
        self,
        instance: object,
        attribute_names: list[str] | None = None,
    ) -> None:
        """Обновляет состояние ORM-объекта из базы данных."""
        if self._session is None:
            raise RuntimeError("UoW not started")

        await self._session.refresh(instance, attribute_names)

    @asynccontextmanager
    async def make_savepoint(self) -> AsyncGenerator[None, None]:
        """Создает вложенную транзакцию."""
        if self._session is None:
            raise RuntimeError("UoW not started")

        async with self._session.begin_nested():
            yield

    def _get_repository(
        self,
        repo_cls: Callable[[AsyncSession], RepositoryType],
    ) -> RepositoryType:
        """Лениво инициализирует репозиторий."""
        if self._session is None:
            raise RuntimeError("UoW not started")

        if repo_cls not in self._repositories:
            self._repositories[repo_cls] = repo_cls(self._session)

        return self._repositories[repo_cls]  # type: ignore[return-value]

    @property
    def categories(self) -> CategoryRepository:
        """Репозиторий категорий."""
        return self._get_repository(CategoryRepository)

    @property
    def rules(self) -> RuleRepository:
        """Репозиторий правил."""
        return self._get_repository(RuleRepository)

    @property
    def results(self) -> ClassificationResultRepository:
        """Репозиторий результатов классификации."""
        return self._get_repository(ClassificationResultRepository)

    @property
    def feedback(self) -> FeedbackRepository:
        """Репозиторий feedback."""
        return self._get_repository(FeedbackRepository)

    @property
    def models(self) -> ModelRepository:
        """Репозиторий ML-моделей."""
        return self._get_repository(ModelRepository)

    @property
    def datasets(self) -> DatasetRepository:
        """Репозиторий датасетов."""
        return self._get_repository(DatasetRepository)

    @property
    def outbox(self) -> OutboxRepository:
        """Репозиторий outbox-событий."""
        return self._get_repository(OutboxRepository)
