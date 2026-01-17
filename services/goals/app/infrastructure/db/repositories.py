import logging
import re
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4
import sqlalchemy as sa
from sqlalchemy import (
    and_,
    case,
    delete,
    func,
    insert,
    select,
    text,
    update,
    or_,
)
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError, DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import exceptions
from app.core.context import get_request_id
from app.domain.enums import GoalStatus
from app.infrastructure.db import models
from app.utils import serialization

logger = logging.getLogger(__name__)

class GoalRepository:
    """Репозиторий для операций с целями."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(
        self,
        user_id: UUID,
        goal_id: UUID,
    ) -> models.Goal | None:
        result = await self.db.execute(
            select(models.Goal).where(
                models.Goal.goal_id == goal_id,
                models.Goal.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_for_update(self, goal_id: UUID) -> models.Goal | None:
        result = await self.db.execute(
            select(models.Goal)
            .where(models.Goal.goal_id == goal_id)
            .with_for_update(nowait=True)
        )
        return result.scalar_one_or_none()

    async def get_main_goals(self, user_id: UUID) -> list[models.Goal]:
        remaining_amount = (
            models.Goal.target_value
            - models.Goal.current_value
        )

        query = (
            select(models.Goal)
            .where(
                models.Goal.user_id == user_id,
                models.Goal.status == GoalStatus.ONGOING.value,
            )
            .order_by(remaining_amount.asc())
            .limit(10)
        )

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_all_goals(
        self,
        user_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> list[models.Goal]:
        """Получение целей с пагинацией."""

        status_priority = case(
            (models.Goal.status == GoalStatus.ONGOING.value, 1),
            (models.Goal.status == GoalStatus.EXPIRED.value, 2),
            (models.Goal.status == GoalStatus.ACHIEVED.value, 3),
            (models.Goal.status == GoalStatus.CLOSED.value, 4),
            else_=5,
        )

        priority_order = case(
            (models.Goal.tags.contains(["High priority"]), 1),
            (models.Goal.tags.contains(["Medium priority"]), 2),
            (models.Goal.tags.contains(["Low priority"]), 3),
            else_=4,
        )

        completion_percentage = case(
            (
                models.Goal.target_value > 0,
                models.Goal.current_value / models.Goal.target_value,
            ),
            else_=0,
        )

        query = (
            select(models.Goal)
            .where(models.Goal.user_id == user_id)
            .order_by(
                status_priority.asc(),
                priority_order.asc(),
                completion_percentage.desc(),
            )
            .limit(limit)
            .offset(offset)
        )

        result = await self.db.execute(query)
        return result.scalars().all()

    def create(self, goal_model: models.Goal) -> models.Goal:
        self.db.add(goal_model)
        return goal_model

    async def adjust_balance(
        self,
        user_id: UUID,
        goal_id: UUID,
        amount: Decimal,
        transaction_id: UUID,
    ) -> models.Goal | None:
        """Обновляет баланс цели."""

        stmt_check = insert(
            models.ProcessedTransaction
        ).values(
            transaction_id=transaction_id,
            goal_id=goal_id,
        )

        try:
            await self.db.execute(stmt_check)

        except IntegrityError:
            return None

        except DBAPIError as e:
            logger.warning(
                "Insert failed, attempting to ensure partition exists. "
                "Error: %s",
                e,
            )

            await self.ensure_current_partition()

            try:
                await self.db.execute(stmt_check)
            except IntegrityError:
                return None

        new_value = sa.func.greatest(
            Decimal(0),
            models.Goal.current_value + amount,
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
                    ]
                ),
            )
            .values(current_value=new_value)
            .execution_options(synchronize_session=False)
            .returning(models.Goal)
        )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_fields(
        self,
        user_id: UUID,
        goal_id: UUID,
        changes: dict,
    ) -> models.Goal:
        stmt = (
            update(models.Goal)
            .where(
                models.Goal.goal_id == goal_id,
                models.Goal.user_id == user_id,
            )
            .values(**changes)
            .returning(models.Goal)
        )

        result = await self.db.execute(stmt)
        goal = result.scalar_one_or_none()

        if goal is None:
            raise exceptions.GoalNotFoundError("Goal not found")

        return goal

    async def mark_achieved_atomically(
        self,
        user_id: UUID,
        goal_id: UUID,
    ) -> models.Goal | None:
        stmt = (
            update(models.Goal)
            .where(
                models.Goal.goal_id == goal_id,
                models.Goal.user_id == user_id,
                models.Goal.status == GoalStatus.ONGOING.value,
                models.Goal.current_value
                >= models.Goal.target_value,
            )
            .values(
                status=GoalStatus.ACHIEVED.value,
                updated_at=func.now(),
            )
            .returning(models.Goal)
        )

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def revert_achievement_atomically(
        self,
        user_id: UUID,
        goal_id: UUID,
    ) -> models.Goal | None:
        stmt = (
            update(models.Goal)
            .where(
                models.Goal.goal_id == goal_id,
                models.Goal.user_id == user_id,
                models.Goal.status == GoalStatus.ACHIEVED.value,
                models.Goal.current_value
                < models.Goal.target_value,
            )
            .values(
                status=GoalStatus.ONGOING.value,
                updated_at=func.now(),
            )
            .returning(models.Goal)
        )

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def bulk_update_status(
        self,
        goal_ids: list[UUID],
        new_status: str,
    ) -> None:
        if not goal_ids:
            return

        stmt = (
            update(models.Goal)
            .where(models.Goal.goal_id.in_(goal_ids))
            .values(
                status=new_status,
                updated_at=datetime.now(timezone.utc),
            )
        )

        await self.db.execute(stmt)

    async def ensure_current_partition(self) -> None:
        """Создаёт партиции на текущий и следующий месяц."""
        today = datetime.now(timezone.utc)

        for offset in (0, 1):
            target_date = today + timedelta(days=32 * offset)
            part_name = (
                f"processed_goal_transactions_"
                f"{target_date.strftime('%Y_%m')}"
            )

            start_date = target_date.replace(day=1).strftime("%Y-%m-%d")

            if target_date.month == 12:
                end_date = f"{target_date.year + 1}-01-01"
            else:
                end_date = (
                    f"{target_date.year}-"
                    f"{target_date.month + 1:02d}-01"
                )

            sql = text(
                f"""
                CREATE TABLE IF NOT EXISTS {part_name}
                PARTITION OF processed_goal_transactions
                FOR VALUES FROM ('{start_date}') TO ('{end_date}');
                """
            )

            await self.db.execute(sql)

    async def drop_old_partitions(self, retention_months: int = 3) -> None:
        logger.warning(
            "Dropping partitions without DETACH CONCURRENTLY. "
            "Potential locking risk."
        )

        result = await self.db.execute(
            text(
                """
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = 'public'
                  AND tablename LIKE 'processed_goal_transactions_____-__'
                """
            )
        )

        tables = result.scalars().all()
        cutoff_date = datetime.now(timezone.utc) - timedelta(
            days=30 * retention_months
        )

        name_pattern = re.compile(
            r"processed_goal_transactions_(\d{4})_(\d{2})"
        )

        for table_name in tables:
            match = name_pattern.search(table_name)
            if not match:
                continue

            year, month = map(int, match.groups())
            partition_date = datetime(
                year,
                month,
                1,
                tzinfo=timezone.utc,
            )

            if partition_date < cutoff_date.replace(day=1):
                logger.info("Dropping old partition: %s", table_name)
                await self.db.execute(
                    text(f"DROP TABLE IF EXISTS {table_name}")
                )

    async def get_expired_goals_batch(
        self,
        today: date,
        limit: int = 100,
        last_id: UUID | None = None,
    ) -> list[models.Goal]:
        query = (
            select(models.Goal)
            .where(
                models.Goal.status == GoalStatus.ONGOING.value,
                models.Goal.finish_date < today,
            )
            .order_by(models.Goal.goal_id.asc())
            .limit(limit)
        )

        if last_id:
            query = query.where(models.Goal.goal_id > last_id)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_approaching_goals_batch(
        self,
        check_date: date,
        limit: int = 100,
    ) -> list[models.Goal]:
        check_datetime_start = datetime.combine(
            check_date,
            datetime.min.time(),
        ).replace(tzinfo=timezone.utc)

        query = (
            select(models.Goal)
            .outerjoin(
                models.GoalNotification,
                and_(
                    models.Goal.goal_id
                    == models.GoalNotification.goal_id,
                    models.GoalNotification.last_checked_date
                    >= check_datetime_start,
                ),
            )
            .where(
                models.Goal.status == GoalStatus.ONGOING.value,
                models.Goal.finish_date.is_not(None),
                models.Goal.finish_date
                <= check_date + timedelta(days=7),
                models.GoalNotification.goal_id.is_(None),
            )
            .limit(limit)
        )

        result = await self.db.execute(query)
        return result.scalars().all()

    async def update_last_checked(self, goal_ids: list[UUID]) -> None:
        if not goal_ids:
            return

        stmt = pg_insert(
            models.GoalNotification
        ).values(
            [
                {
                    "goal_id": goal_id,
                    "last_checked_date": func.now(),
                }
                for goal_id in goal_ids
            ]
        )

        stmt = stmt.on_conflict_do_update(
            index_elements=["goal_id"],
            set_={"last_checked_date": func.now()},
        )

        await self.db.execute(stmt)

    def _prepare_outbox_event(
        self,
        topic: str,
        event_data: dict,
    ) -> dict:
        payload = event_data.get("payload", event_data)

        event_type = event_data.get("event_type")
        if not event_type and isinstance(payload, dict):
            event_type = payload.get("event_type", "unknown")

        clean_payload = serialization.recursive_normalize(payload)
        current_trace_id = get_request_id()

        return {
            "event_id": uuid4(),
            "topic": topic,
            "event_type": event_type,
            "payload": clean_payload,
            "status": "pending",
            "retry_count": 0,
            "created_at": datetime.now(timezone.utc),
            "trace_id": current_trace_id,
            "next_retry_at": None,
        }

    async def add_outbox_events(
        self,
        events: list[dict[str, Any]],
    ) -> None:
        if not events:
            return

        clean_events = [
            self._prepare_outbox_event(
                e["topic"],
                e.get("payload", e),
            )
            for e in events
        ]

        stmt = insert(models.OutboxEvent).values(clean_events)
        await self.db.execute(stmt)

    async def add_outbox_event(
        self,
        topic: str,
        event_data: dict,
    ) -> None:
        await self.add_outbox_events(
            [{"topic": topic, "payload": event_data}]
        )

    async def get_pending_outbox_events(
        self,
        limit: int = 100,
    ) -> list[models.OutboxEvent]:
        """Берёт события, готовые к отправке."""
        now = datetime.now(timezone.utc)

        query = (
            select(models.OutboxEvent)
            .where(
                models.OutboxEvent.status == "pending",
                or_(
                    models.OutboxEvent.next_retry_at.is_(None),
                    models.OutboxEvent.next_retry_at <= now,
                ),
            )
            .order_by(models.OutboxEvent.created_at.asc())
            .limit(limit)
            .with_for_update(skip_locked=True)
        )

        result = await self.db.execute(query)
        return result.scalars().all()

    async def delete_outbox_events(
        self,
        event_ids: list[UUID],
    ) -> None:
        if not event_ids:
            return

        stmt = delete(models.OutboxEvent).where(
            models.OutboxEvent.event_id.in_(event_ids)
        )

        await self.db.execute(stmt)