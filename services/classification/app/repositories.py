import logging
from uuid import UUID
from datetime import datetime, timedelta, timezone
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app import models

logger = logging.getLogger(__name__)

class BaseRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

class CategoryRepository(BaseRepository):
    async def getById(self, categoryId: int) -> models.Category | None:
        return await self.db.get(models.Category, categoryId)

    async def getByName(self, name: str) -> models.Category | None:
        stmt = await self.db.execute(select(models.Category).where(models.Category.name == name))
        return stmt.scalar_one_or_none()

class RuleRepository(BaseRepository):
    @staticmethod
    async def getAllActiveRules(db: AsyncSession) -> list[models.Rule]:
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
    async def getByTransactionId(self, txId: UUID) -> models.ClassificationResult | None:
        stmt = await self.db.execute(
            select(models.ClassificationResult)
            .where(models.ClassificationResult.transactionId == txId)
        )
        return stmt.scalar_one_or_none()

    async def createOrUpdate(
        self, 
        result: models.ClassificationResult
    ) -> models.ClassificationResult:
        """
        Использует ON CONFLICT для атомарного upsert.
        """
        insert_stmt = (
            insert(models.ClassificationResult)
            .values(
                transactionId=result.transactionId,
                categoryId=result.categoryId,
                categoryName=result.categoryName,
                confidence=result.confidence,
                source=result.source,
                modelVersion=result.modelVersion,
                merchant=result.merchant,
                description=result.description,
                mcc=result.mcc,
            )
            .on_conflict_do_update(
                index_elements=[models.ClassificationResult.transactionId],
                set_={
                    "categoryId": result.categoryId,
                    "categoryName": result.categoryName,
                    "confidence": result.confidence,
                    "source": result.source,
                    "modelVersion": result.modelVersion,
                    "merchant": result.merchant,
                    "description": result.description,
                    "mcc": result.mcc,
                },
            )
            .returning(models.ClassificationResult.classificationResultId)
        )

        resultId = await self.db.scalar(insert_stmt)

        stmt = (
            select(models.ClassificationResult)
            .where(models.ClassificationResult.classificationResultId == resultId)
        )

        obj = await self.db.scalar(stmt)

        await self.db.commit()
        return obj

class FeedbackRepository(BaseRepository):
    async def create(self, feedback: models.Feedback) -> models.Feedback:
        self.db.add(feedback)
        await self.db.commit()
        return feedback
        
    async def getAllFeedbackData(self, daysLimit: int = 180) -> list[dict]:
        """
        Получает данные для обучения.
        """
        cutoffDate = datetime.now(timezone.utc) - timedelta(days=daysLimit)
        
        stmt = await self.db.execute(
            select(
                models.ClassificationResult.merchant, 
                models.ClassificationResult.description, 
                models.ClassificationResult.mcc, 
                models.Feedback.correctCategoryId
            )
            .join(
                models.ClassificationResult, 
                models.Feedback.transactionId == models.ClassificationResult.transactionId
            )
            .where(models.Feedback.createdAt >= cutoffDate)
        )
        
        results = stmt.mappings().all()

        return [
            {
                "merchant": row["merchant"],
                "description": row["description"],
                "mcc": row["mcc"],
                "label": int(row["correctCategoryId"])
            }
            for row in results
        ]

class ModelRepository(BaseRepository):
    async def getActiveModel(self) -> models.Model | None:
        stmt = await self.db.execute(select(models.Model).where(models.Model.isActive == True))
        return stmt.scalar_one_or_none()
        
    async def getLatestCandidateModel(self) -> models.Model | None:
        stmt = await self.db.execute(
            select(models.Model)
            .where(models.Model.isActive == False)
            .order_by(models.Model.createdAt.desc())
            .limit(1)
        )
        return stmt.scalar_one_or_none()

    async def createModel(self, model: models.Model) -> models.Model:
        self.db.add(model)
        await self.db.commit()
        return model

    async def promoteModel(self, candidate: models.Model, active: models.Model | None):
        if active:
            active.isActive = False
            self.db.add(active)
        candidate.isActive = True
        self.db.add(candidate)
        await self.db.commit()

class DatasetRepository(BaseRepository):
    async def createDatasetEntry(
        self, 
        dataset: models.TrainingDataset
    ) -> models.TrainingDataset:
        self.db.add(dataset)
        await self.db.commit()
        return dataset
        
    async def getLatestReadyDataset(self) -> models.TrainingDataset | None:
        stmt = await self.db.execute(
            select(models.TrainingDataset)
            .where(models.TrainingDataset.status == models.TrainingDatasetStatus.READY)
            .order_by(models.TrainingDataset.createdAt.desc())
            .limit(1)
        )
        return stmt.scalar_one_or_none()
        
    async def updateDatasetStatus(
        self, 
        dataset: models.TrainingDataset, 
        status: models.TrainingDatasetStatus, 
        metrics: dict
    ):
        dataset.status = status
        dataset.metrics = metrics
        self.db.add(dataset)
        await self.db.commit()