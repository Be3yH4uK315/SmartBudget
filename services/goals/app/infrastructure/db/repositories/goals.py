import logging
import re
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import case, delete, func, insert, select, text, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import exceptions
from app.domain.enums import GoalPriority, GoalStatus, TransactionType
from app.infrastructure.db import models

logger = logging.getLogger(__name__)


class GoalRepository:
    """Репозиторий целей."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(
        self,
        user_id: UUID,
        goal_id: UUID,
    ) -> models.Goal | None:
        """Получает цель пользователя по ID."""
        result = await self.db.execute(
            select(models.Goal).where(
                models.Goal.goal_id == goal_id,
                models.Goal.user_id == user_id,
            ),
        )

        return result.scalar_one_or_none()

    async def get_for_update(self, goal_id: UUID) -> models.Goal | None:
        """Получает цель по ID с блокировкой для обновления."""
        result = await self.db.execute(
            select(models.Goal)
            .where(models.Goal.goal_id == goal_id)
            .with_for_update(nowait=True),
        )

        return result.scalar_one_or_none()

    async def get_main_goals(self, user_id: UUID) -> list[models.Goal]:
        """Получает до 5 основных целей с наименьшим остатком."""
        remaining_amount = models.Goal.target_amount - models.Goal.current_amount

        query = (
            select(models.Goal)
            .where(
                models.Goal.user_id == user_id,
                models.Goal.status == GoalStatus.ONGOING.value,
                models.Goal.is_archived.is_(False),
            )
            .order_by(remaining_amount.asc())
            .limit(5)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def search_goals(
        self,
        user_id: UUID,
        query: str,
        limit_amount: int = 10,
    ) -> list[models.Goal]:
        """Ищет цели пользователя по названию."""
        statement = (
            select(models.Goal)
            .where(
                models.Goal.user_id == user_id,
                models.Goal.name.ilike(f"%{query}%"),
            )
            .order_by(models.Goal.updated_at.desc(), models.Goal.goal_id.asc())
            .limit(limit_amount)
        )

        result = await self.db.execute(statement)
        return list(result.scalars().all())

    async def get_all_goals(
        self,
        user_id: UUID,
        limit_amount: int = 100,
        offset: int = 0,
        tags: list[str] | None = None,
        priorities: list[GoalPriority] | None = None,
        is_archived: bool = False,
    ) -> list[models.Goal]:
        """Получает цели пользователя с фильтрами и сортировкой."""
        status_priority = case(
            (models.Goal.status == GoalStatus.ONGOING.value, 1),
            (models.Goal.status == GoalStatus.EXPIRED.value, 2),
            (models.Goal.status == GoalStatus.ACHIEVED.value, 3),
            (models.Goal.status == GoalStatus.CLOSED.value, 4),
            else_=5,
        )

        priority_order = case(
            (models.Goal.priority == GoalPriority.HIGH.value, 1),
            (models.Goal.priority == GoalPriority.MEDIUM.value, 2),
            (models.Goal.priority == GoalPriority.LOW.value, 3),
            else_=4,
        )

        completion_percentage = case(
            (
                models.Goal.target_amount > 0,
                models.Goal.current_amount / models.Goal.target_amount,
            ),
            else_=0,
        )

        query = select(models.Goal).where(
            models.Goal.user_id == user_id,
            models.Goal.is_archived == is_archived,
        )

        if tags:
            query = query.where(models.Goal.tags.contains(tags))

        if priorities:
            priority_values = [priority.value for priority in priorities]
            query = query.where(models.Goal.priority.in_(priority_values))

        query = (
            query.order_by(
                status_priority.asc(),
                priority_order.asc(),
                completion_percentage.desc(),
            )
            .limit(limit_amount)
            .offset(offset)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    def create(self, goal_model: models.Goal) -> models.Goal:
        """Создает новую цель без commit."""
        self.db.add(goal_model)
        return goal_model

    async def get_net_change_for_current_month(self, goal_id: UUID) -> Decimal:
        """Считает чистое изменение баланса цели с начала текущего месяца."""
        now = datetime.now(timezone.utc)
        start_of_month = now.replace(
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        query = select(
            func.sum(
                case(
                    (
                        models.ProcessedTransaction.transaction_type
                        == TransactionType.INCOME.value,
                        models.ProcessedTransaction.amount,
                    ),
                    else_=-models.ProcessedTransaction.amount,
                ),
            ),
        ).where(
            models.ProcessedTransaction.goal_id == goal_id,
            models.ProcessedTransaction.occurred_at >= start_of_month,
        )

        result = await self.db.execute(query)
        net_change = result.scalar()

        return net_change if net_change is not None else Decimal("0.00")

    async def adjust_balance(
        self,
        user_id: UUID,
        goal_id: UUID,
        amount_delta: Decimal,
        transaction_id: UUID,
        raw_amount: Decimal,
        transaction_type: str,
        occurred_at: datetime,
    ) -> models.Goal | None:
        """Обновляет баланс цели на основе входящей транзакции."""
        insert_transaction = insert(models.ProcessedTransaction).values(
            transaction_id=transaction_id,
            goal_id=goal_id,
            amount=raw_amount,
            transaction_type=transaction_type,
            occurred_at=occurred_at,
        )

        try:
            await self.db.execute(insert_transaction)
        except IntegrityError:
            return None
        except DBAPIError as exc:
            logger.warning(
                "Processed transaction insert failed, trying to ensure partition: %s",
                exc,
                exc_info=True,
            )
            await self.ensure_current_partition()

            try:
                await self.db.execute(insert_transaction)
            except IntegrityError:
                return None

        new_value = sa.func.greatest(
            Decimal("0"),
            models.Goal.current_amount + amount_delta,
        )

        query = (
            update(models.Goal)
            .where(
                models.Goal.goal_id == goal_id,
                models.Goal.user_id == user_id,
                models.Goal.status.in_(
                    [
                        GoalStatus.ONGOING.value,
                        GoalStatus.ACHIEVED.value,
                    ],
                ),
            )
            .values(current_amount=new_value)
            .execution_options(synchronize_session=False)
            .returning(models.Goal)
        )

        result = await self.db.execute(query)
        goal = result.scalar_one_or_none()

        if goal is None:
            await self.db.execute(
                delete(models.ProcessedTransaction).where(
                    models.ProcessedTransaction.transaction_id == transaction_id,
                ),
            )

        return goal

    async def rollback_transaction(
        self,
        user_id: UUID,
        transaction_id: UUID,
    ) -> models.Goal | None:
        """Откатывает ранее обработанную goal-транзакцию."""
        result = await self.db.execute(
            select(models.ProcessedTransaction)
            .where(models.ProcessedTransaction.transaction_id == transaction_id)
            .with_for_update(),
        )
        processed = result.scalar_one_or_none()

        if processed is None:
            return None

        amount_delta = (
            -processed.amount
            if processed.transaction_type == TransactionType.INCOME.value
            else processed.amount
        )

        new_value = sa.func.greatest(
            Decimal("0"),
            models.Goal.current_amount + amount_delta,
        )

        query = (
            update(models.Goal)
            .where(
                models.Goal.goal_id == processed.goal_id,
                models.Goal.user_id == user_id,
                models.Goal.status.in_(
                    [
                        GoalStatus.ONGOING.value,
                        GoalStatus.ACHIEVED.value,
                    ],
                ),
            )
            .values(
                current_amount=new_value,
                updated_at=func.now(),
            )
            .execution_options(synchronize_session=False)
            .returning(models.Goal)
        )

        update_result = await self.db.execute(query)
        goal = update_result.scalar_one_or_none()

        if goal is None:
            return None

        await self.db.execute(
            delete(models.ProcessedTransaction).where(
                models.ProcessedTransaction.transaction_id == transaction_id,
            ),
        )

        return goal

    async def update_fields(
        self,
        user_id: UUID,
        goal_id: UUID,
        changes: dict,
    ) -> models.Goal:
        """Обновляет поля цели и возвращает обновленную модель."""
        result = await self.db.execute(
            update(models.Goal)
            .where(
                models.Goal.goal_id == goal_id,
                models.Goal.user_id == user_id,
            )
            .values(**changes)
            .returning(models.Goal),
        )

        goal = result.scalar_one_or_none()
        if goal is None:
            raise exceptions.GoalNotFoundError("Goal not found")

        return goal

    async def mark_achieved_atomically(
        self,
        user_id: UUID,
        goal_id: UUID,
    ) -> models.Goal | None:
        """Атомарно переводит цель в achieved."""
        result = await self.db.execute(
            update(models.Goal)
            .where(
                models.Goal.goal_id == goal_id,
                models.Goal.user_id == user_id,
                models.Goal.status == GoalStatus.ONGOING.value,
                models.Goal.current_amount >= models.Goal.target_amount,
            )
            .values(
                status=GoalStatus.ACHIEVED.value,
                updated_at=func.now(),
            )
            .returning(models.Goal),
        )

        return result.scalar_one_or_none()

    async def revert_achievement_atomically(
        self,
        user_id: UUID,
        goal_id: UUID,
    ) -> models.Goal | None:
        """Атомарно возвращает achieved-цель в ongoing."""
        result = await self.db.execute(
            update(models.Goal)
            .where(
                models.Goal.goal_id == goal_id,
                models.Goal.user_id == user_id,
                models.Goal.status == GoalStatus.ACHIEVED.value,
                models.Goal.current_amount < models.Goal.target_amount,
            )
            .values(
                status=GoalStatus.ONGOING.value,
                updated_at=func.now(),
            )
            .returning(models.Goal),
        )

        return result.scalar_one_or_none()

    async def bulk_update_status(
        self,
        goal_ids: list[UUID],
        new_status: str,
    ) -> None:
        """Массово обновляет статус целей."""
        if not goal_ids:
            return

        await self.db.execute(
            update(models.Goal)
            .where(models.Goal.goal_id.in_(goal_ids))
            .values(
                status=new_status,
                updated_at=datetime.now(timezone.utc),
            ),
        )

    async def ensure_current_partition(self) -> None:
        """Создает партиции processed_goal_transactions на текущий и следующий месяц."""
        today = datetime.now(timezone.utc)

        for offset in (0, 1):
            target_date = today + timedelta(days=32 * offset)
            partition_name = f"processed_goal_transactions_{target_date:%Y_%m}"

            start_date = target_date.replace(day=1).strftime("%Y-%m-%d")
            end_date = _get_next_month_start(target_date)

            await self.db.execute(
                text(
                    f"""
                    CREATE TABLE IF NOT EXISTS {partition_name}
                    PARTITION OF processed_goal_transactions
                    FOR VALUES FROM ('{start_date}') TO ('{end_date}');
                    """,
                ),
            )

    async def drop_old_partitions(self, retention_months: int = 3) -> None:
        """Удаляет старые партиции processed_goal_transactions."""
        logger.warning(
            "Dropping partitions without DETACH CONCURRENTLY. Potential locking risk.",
        )

        result = await self.db.execute(
            text(
                """
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = 'public'
                  AND tablename LIKE 'processed_goal_transactions_____-__'
                """,
            ),
        )

        tables = result.scalars().all()
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=30 * retention_months)
        partition_name_pattern = re.compile(
            r"processed_goal_transactions_(\d{4})_(\d{2})",
        )

        for table_name in tables:
            match = partition_name_pattern.search(table_name)
            if not match:
                continue

            year, month = map(int, match.groups())
            partition_date = datetime(year, month, 1, tzinfo=timezone.utc)

            if partition_date < cutoff_date.replace(day=1):
                logger.info("Dropping old partition: %s", table_name)
                await self.db.execute(text(f"DROP TABLE IF EXISTS {table_name}"))

    async def get_expired_goals_batch(
        self,
        today: date,
        limit_amount: int = 100,
        last_id: UUID | None = None,
    ) -> list[models.Goal]:
        """Получает batch целей, срок которых истек до today."""
        query = (
            select(models.Goal)
            .where(
                models.Goal.status == GoalStatus.ONGOING.value,
                models.Goal.finish_date < today,
                models.Goal.is_archived.is_(False),
            )
            .order_by(models.Goal.goal_id.asc())
            .limit(limit_amount)
        )

        if last_id:
            query = query.where(models.Goal.goal_id > last_id)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_approaching_goals_batch(
        self,
        check_date: date,
        limit_amount: int = 100,
    ) -> list[models.Goal]:
        """Получает цели, срок которых истекает в течение недели."""
        query = (
            select(models.Goal)
            .outerjoin(
                models.GoalNotification,
                models.Goal.goal_id == models.GoalNotification.goal_id,
            )
            .where(
                models.Goal.status == GoalStatus.ONGOING.value,
                models.Goal.is_archived.is_(False),
                models.Goal.finish_date.is_not(None),
                models.Goal.finish_date <= check_date + timedelta(days=7),
                models.GoalNotification.goal_id.is_(None),
            )
            .limit(limit_amount)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_goals_without_income_batch(
        self,
        period_start: datetime,
        period_end: datetime,
        limit_amount: int = 100,
        last_id: UUID | None = None,
    ) -> list[models.Goal]:
        """Получает ongoing-цели без income-транзакций за период."""
        income_exists = (
            select(models.ProcessedTransaction.transaction_id)
            .where(
                models.ProcessedTransaction.goal_id == models.Goal.goal_id,
                models.ProcessedTransaction.transaction_type
                == TransactionType.INCOME.value,
                models.ProcessedTransaction.occurred_at >= period_start,
                models.ProcessedTransaction.occurred_at < period_end,
            )
            .exists()
        )

        query = (
            select(models.Goal)
            .where(
                models.Goal.status == GoalStatus.ONGOING.value,
                models.Goal.is_archived.is_(False),
                models.Goal.created_at < period_start,
                ~income_exists,
            )
            .order_by(models.Goal.goal_id.asc())
            .limit(limit_amount)
        )

        if last_id:
            query = query.where(models.Goal.goal_id > last_id)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_last_checked(self, goal_ids: list[UUID]) -> None:
        """Обновляет дату последней проверки уведомлений по целям."""
        if not goal_ids:
            return

        statement = pg_insert(models.GoalNotification).values(
            [
                {
                    "goal_id": goal_id,
                    "last_checked_at": func.now(),
                }
                for goal_id in goal_ids
            ],
        )

        statement = statement.on_conflict_do_update(
            index_elements=["goal_id"],
            set_={"last_checked_at": func.now()},
        )

        await self.db.execute(statement)

    async def reset_notification_state(self, goal_id: UUID) -> None:
        """Сбрасывает состояние deadline-уведомлений по цели."""
        await self.db.execute(
            delete(models.GoalNotification).where(
                models.GoalNotification.goal_id == goal_id,
            ),
        )


def _get_next_month_start(target_date: datetime) -> str:
    """Возвращает первый день следующего месяца в формате YYYY-MM-DD."""
    if target_date.month == 12:
        return f"{target_date.year + 1}-01-01"

    return f"{target_date.year}-{target_date.month + 1:02d}-01"
