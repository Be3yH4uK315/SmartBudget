from uuid import UUID

from sqlalchemy import select

from app.infrastructure.db.models import (
    ClassificationModel,
    TrainingDataset,
    TrainingDatasetStatus,
)
from app.infrastructure.db.repositories.base import BaseRepository


class ModelRepository(BaseRepository):
    """Репозиторий ML-моделей."""

    async def get_active_model(self) -> ClassificationModel | None:
        """Получает активную модель."""
        result = await self.db.execute(
            select(ClassificationModel).where(
                ClassificationModel.is_active.is_(True),
            ),
        )

        return result.scalar_one_or_none()

    async def get_latest_candidate(self) -> ClassificationModel | None:
        """Получает последнюю кандидат-модель."""
        result = await self.db.execute(
            select(ClassificationModel)
            .where(ClassificationModel.is_active.is_(False))
            .order_by(ClassificationModel.created_at.desc())
            .limit(1),
        )

        return result.scalar_one_or_none()

    def create(self, model: ClassificationModel) -> ClassificationModel:
        """Добавляет новую модель в текущую сессию без commit."""
        self.db.add(model)

        return model

    def promote(
        self,
        candidate: ClassificationModel,
        active: ClassificationModel | None,
    ) -> None:
        """Переводит кандидат-модель в активные."""
        if active:
            active.is_active = False
            self.db.add(active)

        candidate.is_active = True
        self.db.add(candidate)


class DatasetRepository(BaseRepository):
    """Репозиторий обучающих датасетов."""

    def create(self, dataset: TrainingDataset) -> TrainingDataset:
        """Добавляет датасет в текущую сессию без commit."""
        self.db.add(dataset)

        return dataset

    async def get_by_id(self, ds_id: UUID) -> TrainingDataset | None:
        """Получает датасет по ID."""
        return await self.db.get(TrainingDataset, ds_id)

    async def get_latest_ready(self) -> TrainingDataset | None:
        """Получает последний готовый датасет."""
        result = await self.db.execute(
            select(TrainingDataset)
            .where(TrainingDataset.status == TrainingDatasetStatus.READY)
            .order_by(TrainingDataset.created_at.desc())
            .limit(1),
        )

        return result.scalar_one_or_none()

    async def update_status(
        self,
        dataset: TrainingDataset,
        status: TrainingDatasetStatus,
        metrics: dict,
    ) -> None:
        """Обновляет статус и метрики датасета."""
        dataset.status = status
        dataset.metrics = metrics
        self.db.add(dataset)
