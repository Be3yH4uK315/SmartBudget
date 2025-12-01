import logging
from uuid import UUID
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from app import models

logger = logging.getLogger(__name__)

class BaseRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

class CategoryRepository(BaseRepository):
    async def get_by_id(self, category_id: UUID) -> models.Category | None:
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
        self.db.add(result)
        await self.db.commit()
        return result

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
        feedback_list = []
        batch_size = 1000
        offset = 0
        while True:
            feedback_query = await self.db.execute(
                select(models.Feedback).order_by(models.Feedback.id).limit(batch_size).offset(offset)
            )
            batch = feedback_query.scalars().all()
            if not batch:
                break
            feedback_list.extend(batch)
            offset += batch_size
        
        if not feedback_list:
            return []

        data_for_training = []
        for i in range(0, len(feedback_list), batch_size):
            batch_fb = feedback_list[i:i+batch_size]
            feedback_transaction_ids = [fb.transaction_id for fb in batch_fb]
            
            results_stmt = await self.db.execute(
                select(models.ClassificationResult)
                .where(models.ClassificationResult.transaction_id.in_(feedback_transaction_ids))
            )
            results_map = {res.transaction_id: res for res in results_stmt.scalars().all()}
            
            for fb in batch_fb:
                result_data = results_map.get(fb.transaction_id)
                if not result_data:
                    logger.warning(f"No ClassificationResult for feedback {fb.id}. Skipping.")
                    continue

                data_for_training.append({
                    "merchant": result_data.merchant,
                    "description": result_data.description,
                    "mcc": result_data.mcc,
                    "label": str(fb.correct_category_id)
                })
        return data_for_training

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
        candidate.is_active = True
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
        await self.db.commit()