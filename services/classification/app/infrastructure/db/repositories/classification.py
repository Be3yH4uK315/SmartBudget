from collections.abc import AsyncGenerator
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, or_, select, update
from sqlalchemy.dialects.postgresql import insert

from app.infrastructure.db.models import (
    ClassificationResult,
    ClassificationSource,
    Feedback,
)
from app.infrastructure.db.repositories.base import BaseRepository

ML_LOW_CONFIDENCE_THRESHOLD = 0.8
UNCATEGORIZED_CATEGORY_ID = 1


class ClassificationResultRepository(BaseRepository):
    """Репозиторий результатов классификации."""

    async def get_by_transaction_id(
        self,
        tx_id: UUID,
    ) -> ClassificationResult | None:
        """Получает результат классификации по ID транзакции."""
        result = await self.db.execute(
            select(ClassificationResult).where(
                ClassificationResult.transaction_id == tx_id,
            ),
        )

        return result.scalar_one_or_none()

    async def get_user_result(
        self,
        user_id: UUID,
        tx_id: UUID,
    ) -> ClassificationResult | None:
        """Получает результат классификации владельца транзакции."""
        result = await self.db.execute(
            select(ClassificationResult).where(
                ClassificationResult.user_id == user_id,
                ClassificationResult.transaction_id == tx_id,
            ),
        )

        return result.scalar_one_or_none()

    async def upsert(self, result: ClassificationResult) -> ClassificationResult:
        """Атомарно создает или обновляет результат классификации."""
        insert_stmt = (
            insert(ClassificationResult)
            .values(
                transaction_id=result.transaction_id,
                user_id=result.user_id,
                category_id=result.category_id,
                category_name_snapshot=result.category_name_snapshot,
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
                    "user_id": result.user_id,
                    "category_name_snapshot": result.category_name_snapshot,
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
        """Возвращает множество transaction_id, которые уже есть в базе."""
        if not tx_ids:
            return set()

        result = await self.db.execute(
            select(ClassificationResult.transaction_id).where(
                ClassificationResult.transaction_id.in_(tx_ids),
            ),
        )

        return set(result.scalars().all())

    async def count_by_user_and_category(
        self,
        user_id: UUID,
        category_id: int,
    ) -> int:
        """Считает результаты классификации пользователя по категории."""
        result = await self.db.scalar(
            select(func.count()).where(
                ClassificationResult.user_id == user_id,
                ClassificationResult.category_id == category_id,
            ),
        )

        return result or 0


class FeedbackRepository(BaseRepository):
    """Репозиторий пользовательского feedback."""

    def create(self, feedback: Feedback) -> Feedback:
        """Добавляет feedback в текущую сессию без commit."""
        self.db.add(feedback)

        return feedback

    async def get_training_data(self, days_limit: int = 180) -> list[dict]:
        """Получает данные для обучения."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_limit)

        result = await self.db.execute(
            select(
                ClassificationResult.merchant,
                ClassificationResult.description,
                ClassificationResult.mcc,
                Feedback.correct_category_id,
            )
            .join(
                ClassificationResult,
                Feedback.transaction_id == ClassificationResult.transaction_id,
            )
            .where(
                Feedback.created_at >= cutoff_date,
                Feedback.correct_category_id != UNCATEGORIZED_CATEGORY_ID,
                or_(
                    ClassificationResult.source.in_(
                        [
                            ClassificationSource.ML,
                            ClassificationSource.MANUAL,
                        ],
                    ),
                    ClassificationResult.confidence < ML_LOW_CONFIDENCE_THRESHOLD,
                ),
            ),
        )

        return [
            {
                "merchant": row["merchant"],
                "description": row["description"],
                "mcc": row["mcc"],
                "label": int(row["correct_category_id"]),
            }
            for row in result.mappings().all()
        ]

    async def stream_training_data(
        self,
        days_limit: int = 180,
        batch_size: int = 1000,
    ) -> AsyncGenerator[list[dict], None]:
        """Стримит данные для обучения пачками."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_limit)

        stmt = (
            select(
                ClassificationResult.merchant,
                ClassificationResult.description,
                ClassificationResult.mcc,
                Feedback.correct_category_id,
            )
            .join(
                ClassificationResult,
                Feedback.transaction_id == ClassificationResult.transaction_id,
            )
            .where(
                Feedback.created_at >= cutoff_date,
                Feedback.correct_category_id != UNCATEGORIZED_CATEGORY_ID,
                or_(
                    ClassificationResult.source.in_(
                        [
                            ClassificationSource.ML,
                            ClassificationSource.MANUAL,
                        ],
                    ),
                    ClassificationResult.confidence < ML_LOW_CONFIDENCE_THRESHOLD,
                ),
            )
            .order_by(Feedback.created_at.asc())
        )

        result = await self.db.stream(stmt)

        while True:
            chunk = await result.fetchmany(batch_size)
            if not chunk:
                break

            yield [
                {
                    "merchant": row.merchant,
                    "description": row.description,
                    "mcc": row.mcc,
                    "label": int(row.correct_category_id),
                }
                for row in chunk
            ]

    async def mark_unprocessed_as_processed(self) -> int:
        """Помечает все необработанные feedback-записи как обработанные."""
        result = await self.db.execute(
            update(Feedback)
            .where(Feedback.processed.is_(False))
            .values(processed=True),
        )

        return result.rowcount
