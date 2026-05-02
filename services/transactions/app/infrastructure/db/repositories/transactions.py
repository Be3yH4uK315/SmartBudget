from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import type_to_db
from app.infrastructure.db import models


class TransactionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    def create(self, transaction: models.Transaction) -> models.Transaction:
        self.db.add(transaction)
        return transaction

    async def exists(self, transaction_id: UUID) -> bool:
        result = await self.db.execute(
            select(models.Transaction.id).where(
                models.Transaction.transaction_id == transaction_id,
            )
        )
        return result.scalar_one_or_none() is not None

    async def get_by_transaction_id(
        self,
        transaction_id: UUID,
    ) -> models.Transaction | None:
        result = await self.db.execute(
            select(models.Transaction).where(
                models.Transaction.transaction_id == transaction_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_user_transaction(
        self,
        user_id: UUID,
        transaction_id: UUID,
    ) -> models.Transaction | None:
        result = await self.db.execute(
            select(models.Transaction).where(
                models.Transaction.user_id == user_id,
                models.Transaction.transaction_id == transaction_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_for_update(
        self,
        transaction_id: UUID,
    ) -> models.Transaction | None:
        result = await self.db.execute(
            select(models.Transaction)
            .where(models.Transaction.transaction_id == transaction_id)
            .with_for_update()
        )
        return result.scalar_one_or_none()

    async def get_user_transaction_for_update(
        self,
        user_id: UUID,
        transaction_id: UUID,
    ) -> models.Transaction | None:
        result = await self.db.execute(
            select(models.Transaction)
            .where(
                models.Transaction.user_id == user_id,
                models.Transaction.transaction_id == transaction_id,
            )
            .with_for_update()
        )
        return result.scalar_one_or_none()

    async def list_user_transactions(
        self,
        user_id: UUID,
        limit: int,
        offset: int,
        category_ids: list[int] | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        transaction_type: str | None = None,
        value_from: Decimal | None = None,
        value_to: Decimal | None = None,
    ) -> list[models.Transaction]:
        query = select(models.Transaction).where(models.Transaction.user_id == user_id)

        if category_ids:
            query = query.where(models.Transaction.category_id.in_(category_ids))

        if date_from:
            query = query.where(models.Transaction.created_at >= date_from)

        if date_to:
            query = query.where(models.Transaction.created_at <= date_to)

        if transaction_type:
            query = query.where(models.Transaction.type == type_to_db(transaction_type))

        absolute_value = func.abs(models.Transaction.value)

        if value_from is not None:
            query = query.where(absolute_value >= value_from)

        if value_to is not None:
            query = query.where(absolute_value <= value_to)

        query = (
            query.order_by(models.Transaction.created_at.desc())
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
            .order_by(models.Transaction.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def delete_by_transaction_id(self, transaction_id: UUID) -> models.Transaction | None:
        transaction = await self.get_for_update(transaction_id)
        if not transaction:
            return None

        await self.db.execute(
            delete(models.Transaction).where(
                models.Transaction.transaction_id == transaction_id,
            )
        )
        return transaction

    async def delete_user_transaction(
        self,
        user_id: UUID,
        transaction_id: UUID,
    ) -> models.Transaction | None:
        transaction = await self.get_user_transaction_for_update(user_id, transaction_id)
        if not transaction:
            return None

        await self.db.execute(
            delete(models.Transaction).where(
                models.Transaction.user_id == user_id,
                models.Transaction.transaction_id == transaction_id,
            )
        )
        return transaction

    async def aggregate_by_month_for_account(
        self,
        user_id: UUID,
        account_id: UUID,
    ) -> list[tuple[Decimal, datetime, int]]:
        month = func.date_trunc("month", models.Transaction.created_at).label("month")
        query = (
            select(
                func.sum(models.Transaction.value).label("value"),
                month,
                models.Transaction.type,
            )
            .where(
                models.Transaction.user_id == user_id,
                models.Transaction.account_id == account_id,
            )
            .group_by(month, models.Transaction.type)
            .order_by(month.desc(), models.Transaction.type.asc())
        )

        result = await self.db.execute(query)
        return [(row.value, row.month, row.type) for row in result.all()]
