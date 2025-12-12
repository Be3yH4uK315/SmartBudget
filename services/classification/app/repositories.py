import logging
from uuid import UUID
from sqlalchemy import insert
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from app import models

logger = logging.getLogger(__name__)

class BaseRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

class CategoryRepository(BaseRepository):
    async def get_by_id(self, category_id: int) -> models.Category | None:
        return await self.db.get(models.Category, category_id)

    async def get_by_name(self, name: str) -> models.Category | None:
        stmt = await self.db.execute(select(models.Category).where(models.Category.name == name))
        return stmt.scalar_one_or_none()

class RuleRepository(BaseRepository):
    @staticmethod
    async def get_all_active_rules(db: AsyncSession) -> list[models.Rule]:
        """
        Загружает все правила. 
        """
        logger.info("Cache MISS: Loading rules from database...")
        stmt = await db.execute(
            select(models.Rule)
            .options(joinedload(models.Rule.category))
            .order_by(models.Rule.priority.asc())
        )
        return stmt.scalars().all()

class ClassificationResultRepository(BaseRepository):
    async def get_by_transaction_id(self, tx_id: UUID) -> models.ClassificationResult | None:
        stmt = await self.db.execute(
            select(models.ClassificationResult).where(models.ClassificationResult.transaction_id == tx_id)
        )
        return stmt.scalar_one_or_none()

    async def create_or_update(self, result: models.ClassificationResult) -> models.ClassificationResult:
        """
        Использует ON CONFLICT для атомарного upsert.
        """
        stmt = insert(models.ClassificationResult).values(
            transaction_id=result.transaction_id,
            category_id=result.category_id,
            category_name=result.category_name,
            confidence=result.confidence,
            source=result.source,
            model_version=result.model_version,
            merchant=result.merchant,
            description=result.description,
            mcc=result.mcc,
            created_at=result.created_at
        ).on_conflict_do_update(
            index_elements=['transaction_id'],
            set_={
                "category_id": result.category_id,
                "category_name": result.category_name,
                "confidence": result.confidence,
                "source": result.source,
                "model_version": result.model_version,
                "merchant": result.merchant,
                "description": result.description
            }
        ).returning(models.ClassificationResult)

        orm_stmt = select(models.ClassificationResult).from_statement(stmt)
        res = await self.db.execute(orm_stmt)
        updated_obj = res.scalar_one()
        
        await self.db.commit()
        return updated_obj

class FeedbackRepository(BaseRepository):
    async def create(self, feedback: models.Feedback) -> models.Feedback:
        self.db.add(feedback)
        await self.db.commit()
        return feedback
        
    async def get_all_feedback_data(self) -> list[dict]:
        """
        Сложный запрос для build_dataset_task.
        Объединяет Feedback и ClassificationResult.
        """
        stmt = await self.db.execute(
            select(
                models.ClassificationResult.merchant, 
                models.ClassificationResult.description, 
                models.ClassificationResult.mcc, 
                models.Feedback.correct_category_id
            )
            .join(
                models.ClassificationResult, 
                models.Feedback.transaction_id == models.ClassificationResult.transaction_id
            )
        )
        
        results = stmt.mappings().all()

        return [
            {
                "merchant": row["merchant"],
                "description": row["description"],
                "mcc": row["mcc"],
                "label": int(row["correct_category_id"])
            }
            for row in results
        ]

class ModelRepository(BaseRepository):
    async def get_active_model(self) -> models.Model | None:
        stmt = await self.db.execute(select(models.Model).where(models.Model.is_active == True))
        return stmt.scalar_one_or_none()
        
    async def get_latest_candidate_model(self) -> models.Model | None:
        stmt = await self.db.execute(
            select(models.Model)
            .where(models.Model.is_active == False)
            .order_by(models.Model.created_at.desc())
            .limit(1)
        )
        return stmt.scalar_one_or_none()

    async def create_model(self, model: models.Model) -> models.Model:
        self.db.add(model)
        await self.db.commit()
        return model

    async def promote_model(self, candidate: models.Model, active: models.Model | None):
        if active:
            active.is_active = False
            self.db.add(active)
        candidate.is_active = True
        self.db.add(candidate)
        await self.db.commit()

class DatasetRepository(BaseRepository):
    async def create_dataset_entry(self, dataset: models.TrainingDataset) -> models.TrainingDataset:
        self.db.add(dataset)
        await self.db.commit()
        return dataset
        
    async def get_latest_ready_dataset(self) -> models.TrainingDataset | None:
        stmt = await self.db.execute(
            select(models.TrainingDataset)
            .where(models.TrainingDataset.status == models.TrainingDatasetStatus.READY)
            .order_by(models.TrainingDataset.created_at.desc())
            .limit(1)
        )
        return stmt.scalar_one_or_none()
        
    async def update_dataset_status(self, dataset: models.TrainingDataset, status: models.TrainingDatasetStatus, metrics: dict):
        dataset.status = status
        dataset.metrics = metrics
        self.db.add(dataset)
        await self.db.commit()