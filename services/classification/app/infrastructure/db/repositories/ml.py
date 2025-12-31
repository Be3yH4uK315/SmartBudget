from uuid import UUID
from sqlalchemy import select

from app.infrastructure.db.models import Model, TrainingDataset, TrainingDatasetStatus
from app.infrastructure.db.repositories.base import BaseRepository

class ModelRepository(BaseRepository):
    async def get_active_model(self) -> Model | None:
        """Получает активную модель."""
        stmt = select(Model).where(Model.is_active == True)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
        
    async def get_latest_candidate(self) -> Model | None:
        """Получает последнюю кандидат-модель."""
        stmt = (
            select(Model)
            .where(Model.is_active == False)
            .order_by(Model.created_at.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    def create(self, model: Model) -> Model:
        """Создает новую модель."""
        self.db.add(model)
        return model

    def promote(self, candidate: Model, active: Model | None):
        """Переводит кандидат в активные, деактивирует старую."""
        if active:
            active.is_active = False
            self.db.add(active)
        candidate.is_active = True
        self.db.add(candidate)

class DatasetRepository(BaseRepository):
    def create(self, dataset: TrainingDataset) -> TrainingDataset: 
        """Создает запись о датасете."""
        self.db.add(dataset)
        return dataset
    
    async def get_by_id(self, ds_id: UUID) -> TrainingDataset | None:
        """Получает датасет по ID."""
        return await self.db.get(TrainingDataset, ds_id)
        
    async def get_latest_ready(self) -> TrainingDataset | None:
        """Получает последний готовый датасет."""
        stmt = (
            select(TrainingDataset)
            .where(TrainingDataset.status == TrainingDatasetStatus.READY)
            .order_by(TrainingDataset.created_at.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
        
    async def update_status(
        self, 
        dataset: TrainingDataset, 
        status: TrainingDatasetStatus, 
        metrics: dict
    ):
        """Обновляет статус и метрики датасета."""
        dataset.status = status
        dataset.metrics = metrics
        self.db.add(dataset)