from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.enums import TransactionType
from app.infrastructure.db import models


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _amount_delta(amount: Decimal, transaction_type: TransactionType | str) -> Decimal:
    tx_type = (
        transaction_type
        if isinstance(transaction_type, TransactionType)
        else TransactionType(transaction_type)
    )
    return amount if tx_type == TransactionType.EXPENSE else -amount


class BudgetRepository:
    """Репозиторий для операций с бюджетами."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_user_month(
        self,
        user_id: UUID,
        month: date,
    ) -> models.Budget | None:
        result = await self.db.execute(
            select(models.Budget)
            .where(
                models.Budget.user_id == user_id,
                models.Budget.month == month,
            )
            .options(selectinload(models.Budget.category_limits))
        )
        return result.scalar_one_or_none()

    async def get_by_user_id_for_update(
        self,
        user_id: UUID,
        month: date | None = None,
    ) -> models.Budget | None:
        filters = [models.Budget.user_id == user_id]
        if month is not None:
            filters.append(models.Budget.month == month)

        query = (
            select(models.Budget)
            .where(*filters)
            .options(selectinload(models.Budget.category_limits))
            .order_by(models.Budget.created_at.desc())
            .limit(1)
            .with_for_update()
        )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_user_month_for_update(
        self,
        user_id: UUID,
        month: date,
    ) -> models.Budget | None:
        result = await self.db.execute(
            select(models.Budget)
            .where(
                models.Budget.user_id == user_id,
                models.Budget.month == month,
            )
            .options(selectinload(models.Budget.category_limits))
            .with_for_update()
        )
        return result.scalar_one_or_none()

    async def list_auto_renew_budgets(
        self,
        month: date,
        limit: int,
    ) -> list[models.Budget]:
        result = await self.db.execute(
            select(models.Budget)
            .where(
                models.Budget.month == month,
                models.Budget.is_auto_renew.is_(True),
            )
            .options(selectinload(models.Budget.category_limits))
            .order_by(models.Budget.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    def create(self, budget: models.Budget) -> models.Budget:
        self.db.add(budget)
        return budget

    async def get_processed_transaction(
        self,
        transaction_id: UUID,
    ) -> models.ProcessedBudgetTransaction | None:
        result = await self.db.execute(
            select(models.ProcessedBudgetTransaction)
            .where(models.ProcessedBudgetTransaction.transaction_id == transaction_id)
            .with_for_update()
        )
        return result.scalar_one_or_none()

    def add_processed_transaction(
        self,
        transaction_id: UUID,
        user_id: UUID,
        month: date,
        category_id: int | None,
        amount: Decimal,
        transaction_type: TransactionType,
        occurred_at: datetime,
    ) -> models.ProcessedBudgetTransaction:
        processed = models.ProcessedBudgetTransaction(
            transaction_id=transaction_id,
            user_id=user_id,
            month=month,
            category_id=category_id,
            amount=amount,
            transaction_type=transaction_type.value,
            occurred_at=occurred_at,
            created_at=_utc_now(),
            updated_at=_utc_now(),
        )
        self.db.add(processed)
        return processed

    async def delete_processed_transaction(self, transaction_id: UUID) -> None:
        await self.db.execute(
            sa.delete(models.ProcessedBudgetTransaction).where(
                models.ProcessedBudgetTransaction.transaction_id == transaction_id,
            )
        )

    def get_or_create_category(
        self,
        budget: models.Budget,
        category_id: int,
    ) -> models.CategoryLimit:
        for category in budget.category_limits:
            if category.category_id == category_id:
                return category

        now = _utc_now()
        category = models.CategoryLimit(
            category_limit_id=uuid4(),
            budget_id=budget.budget_id,
            category_id=category_id,
            limit_amount=Decimal("0.00"),
            spent_amount=Decimal("0.00"),
            created_at=now,
            updated_at=now,
        )
        budget.category_limits.append(category)
        return category

    def adjust_category_spent(
        self,
        budget: models.Budget,
        category_id: int | None,
        amount: Decimal,
        transaction_type: TransactionType,
        multiplier: int = 1,
    ) -> models.CategoryLimit | None:
        if category_id is None:
            return None

        category = self.get_or_create_category(budget, category_id)
        delta = _amount_delta(amount, transaction_type) * multiplier
        category.spent_amount = max(
            Decimal("0.00"),
            category.spent_amount + delta,
        )
        tx_type = (
            transaction_type
            if isinstance(transaction_type, TransactionType)
            else TransactionType(transaction_type)
        )
        if tx_type == TransactionType.INCOME:
            budget.total_income_amount = max(
                Decimal("0.00"),
                budget.total_income_amount + amount * multiplier,
            )
        category.updated_at = _utc_now()
        budget.updated_at = _utc_now()
        return category
