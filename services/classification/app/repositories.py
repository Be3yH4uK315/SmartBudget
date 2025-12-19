import logging
from uuid import UUID
from datetime import datetime, timedelta, timezone
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import SQLAlchemyError

from app import models

logger = logging.getLogger(__name__)

class BaseRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

class CategoryRepository(BaseRepository):
    async def get_by_id(self, category_id: int) -> models.Category | None:
        """Получает категорию по ID."""
        try:
            return await self.db.get(models.Category, category_id)
        except SQLAlchemyError as e:
            logger.error(f"Error getting category by ID: {e}")
            return None

    async def get_by_name(self, name: str) -> models.Category | None:
        """Получает категорию по имени."""
        try:
            stmt = select(models.Category).where(models.Category.name == name)
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Error getting category by name: {e}")
            return None

class RuleRepository(BaseRepository):
    @staticmethod
    async def get_all_active_rules(db: AsyncSession) -> list[dict]:
        """
        Загружает все правила и преобразует в список словарей.
        """
        try:
            logger.debug("Loading rules from database...")
            stmt = (
                select(models.Rule)
                .options(selectinload(models.Rule.category))
                .order_by(models.Rule.priority.asc())
            )
            result = await db.execute(stmt)
            rules = result.scalars().all()
            
            rules_dicts = []
            for rule in rules:
                rule_dict = {
                    "rule_id": str(rule.rule_id),
                    "category_id": rule.category_id,
                    "category_name": rule.category.name,
                    "pattern": rule.pattern,
                    "pattern_type": rule.pattern_type.value,
                    "mcc": rule.mcc,
                    "priority": rule.priority
                }
                rules_dicts.append(rule_dict)
            
            return rules_dicts
        except SQLAlchemyError as e:
            logger.error(f"Error getting all rules: {e}")
            return []

class ClassificationResultRepository(BaseRepository):
    async def get_by_transaction_id(self, tx_id: UUID) -> models.ClassificationResult | None:
        """Получает результат классификации по ID транзакции."""
        try:
            stmt = select(models.ClassificationResult).where(
                models.ClassificationResult.transaction_id == tx_id
            )
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Error getting classification result: {e}")
            return None

    async def create_or_update(
        self, 
        result: models.ClassificationResult
    ) -> models.ClassificationResult:
        """Использует ON CONFLICT для атомарного upsert."""
        try:
            insert_stmt = (
                insert(models.ClassificationResult)
                .values(
                    transaction_id=result.transaction_id,
                    category_id=result.category_id,
                    category_name=result.category_name,
                    confidence=result.confidence,
                    source=result.source,
                    model_version=result.model_version,
                    merchant=result.merchant,
                    description=result.description,
                    mcc=result.mcc,
                )
                .on_conflict_do_update(
                    index_elements=[models.ClassificationResult.transaction_id],
                    set_={
                        "category_id": result.category_id,
                        "category_name": result.category_name,
                        "confidence": result.confidence,
                        "source": result.source,
                        "model_version": result.model_version,
                        "merchant": result.merchant,
                        "description": result.description,
                        "mcc": result.mcc,
                    },
                )
                .returning(models.ClassificationResult.classification_result_id)
            )

            result_id = await self.db.scalar(insert_stmt)
            stmt = select(models.ClassificationResult).where(
                models.ClassificationResult.classification_result_id == result_id
            )
            obj = await self.db.scalar(stmt)
            await self.db.commit()
            return obj
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Error creating/updating classification result: {e}")
            raise

class FeedbackRepository(BaseRepository):
    async def create(self, feedback: models.Feedback) -> models.Feedback:
        """Создает новую обратную связь."""
        try:
            self.db.add(feedback)
            await self.db.commit()
            await self.db.refresh(feedback)
            return feedback
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Error creating feedback: {e}")
            raise
        
    async def get_all_feedback_data(self, days_limit: int = 180) -> list[dict]:
        """Получает данные для обучения (преобразованные в словари)."""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_limit)
            
            stmt = select(
                models.ClassificationResult.merchant, 
                models.ClassificationResult.description, 
                models.ClassificationResult.mcc, 
                models.Feedback.correct_category_id
            ).join(
                models.ClassificationResult, 
                models.Feedback.transaction_id == models.ClassificationResult.transaction_id
            ).where(
                models.Feedback.created_at >= cutoff_date
            )
            
            result = await self.db.execute(stmt)
            rows = result.mappings().all()

            return [
                {
                    "merchant": row["merchant"],
                    "description": row["description"],
                    "mcc": row["mcc"],
                    "label": int(row["correct_category_id"])
                }
                for row in rows
            ]
        except SQLAlchemyError as e:
            logger.error(f"Error getting feedback data: {e}")
            return []

class ModelRepository(BaseRepository):
    async def get_active_model(self) -> models.Model | None:
        """Получает активную модель."""
        try:
            stmt = select(models.Model).where(models.Model.is_active == True)
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Error getting active model: {e}")
            return None
        
    async def get_latest_candidate_model(self) -> models.Model | None:
        """Получает последнюю кандидат-модель."""
        try:
            stmt = (
                select(models.Model)
                .where(models.Model.is_active == False)
                .order_by(models.Model.created_at.desc())
                .limit(1)
            )
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Error getting latest candidate model: {e}")
            return None

    async def create_model(self, model: models.Model) -> models.Model:
        """Создает новую модель."""
        try:
            self.db.add(model)
            await self.db.commit()
            await self.db.refresh(model)
            return model
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Error creating model: {e}")
            raise

    async def promote_model(self, candidate: models.Model, active: models.Model | None):
        """Переводит кандидат в активные, деактивирует старую."""
        try:
            if active:
                active.is_active = False
                self.db.add(active)
            candidate.is_active = True
            self.db.add(candidate)
            await self.db.commit()
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Error promoting model: {e}")
            raise

class DatasetRepository(BaseRepository):
    async def create_dataset_entry(
        self, 
        dataset: models.TrainingDataset
    ) -> models.TrainingDataset:
        """Создает запись о датасете."""
        try:
            self.db.add(dataset)
            await self.db.commit()
            await self.db.refresh(dataset)
            return dataset
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Error creating dataset entry: {e}")
            raise
        
    async def get_latest_ready_dataset(self) -> models.TrainingDataset | None:
        """Получает последний готовый датасет."""
        try:
            stmt = (
                select(models.TrainingDataset)
                .where(models.TrainingDataset.status == models.TrainingDatasetStatus.READY)
                .order_by(models.TrainingDataset.created_at.desc())
                .limit(1)
            )
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Error getting latest ready dataset: {e}")
            return None
        
    async def update_dataset_status(
        self, 
        dataset: models.TrainingDataset, 
        status: models.TrainingDatasetStatus, 
        metrics: dict
    ):
        """Обновляет статус и метрики датасета."""
        try:
            dataset.status = status
            dataset.metrics = metrics
            self.db.add(dataset)
            await self.db.commit()
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Error updating dataset status: {e}")
            raise