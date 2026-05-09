from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db import models


class TransactionRepository:
    """Репозиторий транзакций."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    def create(self, transaction: models.Transaction) -> models.Transaction:
        """Добавляет транзакцию в текущую сессию без commit."""
        self.db.add(transaction)

        return transaction

    async def exists(self, transaction_id: UUID) -> bool:
        """Проверяет существование транзакции по ID."""
        result = await self.db.execute(
            select(models.Transaction.transaction_id).where(
                models.Transaction.transaction_id == transaction_id,
            ),
        )

        return result.scalar_one_or_none() is not None

    async def get_existing_transaction_ids(
        self,
        transaction_ids: list[UUID],
    ) -> set[UUID]:
        """Возвращает множество уже существующих transaction_id."""
        if not transaction_ids:
            return set()

        result = await self.db.execute(
            select(models.Transaction.transaction_id).where(
                models.Transaction.transaction_id.in_(transaction_ids),
            ),
        )

        return set(result.scalars().all())

    async def get_by_transaction_id(
        self,
        transaction_id: UUID,
    ) -> models.Transaction | None:
        """Получает транзакцию по ID."""
        result = await self.db.execute(
            select(models.Transaction).where(
                models.Transaction.transaction_id == transaction_id,
            ),
        )

        return result.scalar_one_or_none()

    async def get_user_transaction(
        self,
        user_id: UUID,
        transaction_id: UUID,
    ) -> models.Transaction | None:
        """Получает транзакцию пользователя."""
        result = await self.db.execute(
            select(models.Transaction).where(
                models.Transaction.user_id == user_id,
                models.Transaction.transaction_id == transaction_id,
            ),
        )

        return result.scalar_one_or_none()

    async def get_for_update(
        self,
        transaction_id: UUID,
    ) -> models.Transaction | None:
        """Получает транзакцию по ID с блокировкой."""
        result = await self.db.execute(
            select(models.Transaction)
            .where(models.Transaction.transaction_id == transaction_id)
            .with_for_update(),
        )

        return result.scalar_one_or_none()

    async def get_user_transaction_for_update(
        self,
        user_id: UUID,
        transaction_id: UUID,
    ) -> models.Transaction | None:
        """Получает транзакцию пользователя с блокировкой."""
        result = await self.db.execute(
            select(models.Transaction)
            .where(
                models.Transaction.user_id == user_id,
                models.Transaction.transaction_id == transaction_id,
            )
            .with_for_update(),
        )

        return result.scalar_one_or_none()

    async def list_user_transactions(
        self,
        user_id: UUID,
        limit: int,
        offset: int,
        category_ids: list[int] | None = None,
        occurred_from: datetime | None = None,
        occurred_to: datetime | None = None,
        transaction_type: str | None = None,
        amount_from: Decimal | None = None,
        amount_to: Decimal | None = None,
    ) -> list[models.Transaction]:
        """Возвращает список транзакций пользователя с фильтрами."""
        query = select(models.Transaction).where(
            models.Transaction.user_id == user_id,
        )

        if category_ids:
            query = query.where(models.Transaction.category_id.in_(category_ids))

        if occurred_from:
            query = query.where(models.Transaction.occurred_at >= occurred_from)

        if occurred_to:
            query = query.where(models.Transaction.occurred_at <= occurred_to)

        if transaction_type:
            query = query.where(models.Transaction.transaction_type == transaction_type)

        absolute_amount = func.abs(models.Transaction.amount)

        if amount_from is not None:
            query = query.where(absolute_amount >= amount_from)

        if amount_to is not None:
            query = query.where(absolute_amount <= amount_to)

        query = (
            query.order_by(models.Transaction.occurred_at.desc())
            .offset(offset)
            .limit(limit)
        )

        result = await self.db.execute(query)

        return list(result.scalars().all())

    async def search_user_transactions(
        self,
        user_id: UUID,
        query_text: str,
        limit: int,
    ) -> list[models.Transaction]:
        """Ищет транзакции пользователя по merchant или description."""
        like = f"%{query_text}%"
        query = (
            select(models.Transaction)
            .where(
                models.Transaction.user_id == user_id,
                or_(
                    models.Transaction.merchant.ilike(like),
                    models.Transaction.description.ilike(like),
                ),
            )
            .order_by(models.Transaction.occurred_at.desc())
            .limit(limit)
        )

        result = await self.db.execute(query)

        return list(result.scalars().all())

    async def delete_by_transaction_id(
        self,
        transaction_id: UUID,
    ) -> models.Transaction | None:
        """Удаляет транзакцию по ID."""
        transaction = await self.get_for_update(transaction_id)
        if not transaction:
            return None

        await self.db.execute(
            delete(models.Transaction).where(
                models.Transaction.transaction_id == transaction_id,
            ),
        )

        return transaction

    async def delete_user_transaction(
        self,
        user_id: UUID,
        transaction_id: UUID,
    ) -> models.Transaction | None:
        """Удаляет транзакцию пользователя."""
        transaction = await self.get_user_transaction_for_update(
            user_id,
            transaction_id,
        )
        if not transaction:
            return None

        await self.db.execute(
            delete(models.Transaction).where(
                models.Transaction.user_id == user_id,
                models.Transaction.transaction_id == transaction_id,
            ),
        )

        return transaction

    async def aggregate_by_month_for_account(
        self,
        user_id: UUID,
        account_id: UUID,
    ) -> list[tuple[Decimal, datetime, str]]:
        """Агрегирует транзакции счета по месяцам и типу."""
        month = func.date_trunc(
            "month",
            models.Transaction.occurred_at,
        ).label("month")

        query = (
            select(
                func.sum(models.Transaction.amount).label("amount"),
                month,
                models.Transaction.transaction_type,
            )
            .where(
                models.Transaction.user_id == user_id,
                models.Transaction.account_id == account_id,
            )
            .group_by(month, models.Transaction.transaction_type)
            .order_by(month.desc(), models.Transaction.transaction_type.asc())
        )

        result = await self.db.execute(query)

        return [
            (row.amount, row.month, row.transaction_type)
            for row in result.all()
        ]
