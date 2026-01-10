from datetime import datetime, timedelta, timezone
from uuid import UUID
from sqlalchemy import select, or_, update
from sqlalchemy.dialects.postgresql import insert

from app.infrastructure.db.models import ClassificationResult, Feedback, ClassificationSource
from app.infrastructure.db.repositories.base import BaseRepository

class ClassificationResultRepository(BaseRepository):
    async def get_by_transaction_id(self, tx_id: UUID) -> ClassificationResult | None:
        """Получает результат классификации по ID транзакции."""
        stmt = select(ClassificationResult).where(ClassificationResult.transaction_id == tx_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert(self, result: ClassificationResult) -> ClassificationResult:
        """Использует ON CONFLICT для атомарного upsert."""
        insert_stmt = (
            insert(ClassificationResult)
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
                index_elements=[ClassificationResult.transaction_id],
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
            .returning(ClassificationResult)
        )
        return await self.db.scalar(insert_stmt)

    async def get_existing_ids(self, tx_ids: list[UUID]) -> set[UUID]:
        """Возвращает set из ID транзакций, которые уже есть в базе."""
        if not tx_ids:
            return set()
            
        stmt = select(ClassificationResult.transaction_id).where(
            ClassificationResult.transaction_id.in_(tx_ids)
        )
        result = await self.db.execute(stmt)
        return set(result.scalars().all())

class FeedbackRepository(BaseRepository):
    def create(self, feedback: Feedback) -> Feedback:
        """Создает новую обратную связь."""
        self.db.add(feedback)
        return feedback
        
    async def get_training_data(self, days_limit: int = 180) -> list[dict]:
        """Получает данные для обучения (преобразованные в словари)."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_limit)
        stmt = select(
            ClassificationResult.merchant, 
            ClassificationResult.description, 
            ClassificationResult.mcc, 
            Feedback.correct_category_id
        ).join(
            ClassificationResult, 
            Feedback.transaction_id == ClassificationResult.transaction_id
        ).where(
            Feedback.created_at >= cutoff_date,
            or_(
                ClassificationResult.source.in_(
                    [ClassificationSource.ML, ClassificationSource.MANUAL]
                ),
                ClassificationResult.confidence < 0.8
            )
        )
        result = await self.db.execute(stmt)
        return [
            {
                "merchant": row["merchant"],
                "description": row["description"],
                "mcc": row["mcc"],
                "label": int(row["correct_category_id"])
            }
            for row in result.mappings().all()
        ]
    
    async def mark_unprocessed_as_processed(self) -> int:
        """Помечает все необработанные записи Feedback как обработанные."""
        stmt = (
            update(Feedback)
            .where(Feedback.processed == False)
            .values(processed=True)
        )
        result = await self.db.execute(stmt)
        return result.rowcount