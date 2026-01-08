import json
import logging
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import delete, insert, or_, select, update, case
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db import models
from app.domain.schemas import api as schemas
from app.core import exceptions
from app.utils import serialization

logger = logging.getLogger(__name__)

class GoalRepository:
    """Репозиторий для операций с целями. Не управляет транзакциями."""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: UUID, goal_id: UUID) -> models.Goal | None:
        """Получает цель по ID и ID пользователя."""
        result = await self.db.execute(
            select(models.Goal).where(
                models.Goal.goal_id == goal_id,
                models.Goal.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    def create(self, goal_model: models.Goal) -> models.Goal:
        """Создает новую цель."""
        self.db.add(goal_model)
        return goal_model

    async def get_main_goals(self, user_id: UUID) -> list[models.Goal]:
        """Получает цели для главного экрана (топ 10 активных)."""
        remaining_amount = models.Goal.target_value - models.Goal.current_value
        query = (
            select(models.Goal)
            .where(
                models.Goal.user_id == user_id,
                models.Goal.status == schemas.GoalStatus.ONGOING.value
            )
            .order_by(remaining_amount.asc())
            .limit(10)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_all_goals(self, user_id: UUID) -> list[models.Goal]:
        """Получает все цели пользователя."""
        status_priority = case(
            (models.Goal.status == schemas.GoalStatus.ONGOING.value, 1),
            (models.Goal.status == schemas.GoalStatus.EXPIRED.value, 2),
            (models.Goal.status == schemas.GoalStatus.ACHIEVED.value, 3),
            (models.Goal.status == schemas.GoalStatus.CLOSED.value, 4),
            else_=5
        )
        completion_percentage = case(
            (models.Goal.target_value > 0, models.Goal.current_value / models.Goal.target_value),
            else_=0
        )

        query = (
            select(models.Goal)
            .where(models.Goal.user_id == user_id)
            .order_by(
                status_priority.asc(),
                completion_percentage.desc()
            )
        )
        result = await self.db.execute(query)
        return result.scalars().all()
    
    def add_outbox_event(self, topic: str, event_data: dict) -> None:
        """Добавляет событие в Outbox."""
        try:
            event_type = event_data.get("event_type", "unknown")
            clean_payload = serialization.recursive_normalize(event_data)
            outbox_entry = models.OutboxEvent(
                topic=topic,
                event_type=event_type,
                payload=clean_payload,
                status='pending'
            )
            self.db.add(outbox_entry)
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"Failed to serialize outbox event: {e}")
            raise exceptions.InvalidGoalDataError("Event serialization failed")

    async def adjust_balance(
        self, user_id: UUID, 
        goal_id: UUID, 
        amount: Decimal, 
        transaction_id: UUID
    ) -> models.Goal | None:
        """Атомарно изменяет баланс цели с защитой от дублей."""
        stmt_check = insert(models.ProcessedTransaction).values(
            transaction_id=transaction_id,
            goal_id=goal_id
        )
        try:
            await self.db.execute(stmt_check)
        except IntegrityError:
            return None 

        new_value = sa.func.greatest(Decimal(0), models.Goal.current_value + amount)

        query = (
            update(models.Goal)
            .where(models.Goal.goal_id == goal_id, models.Goal.user_id == user_id)
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
        changes: dict
    ) -> models.Goal:
        stmt = (
            update(models.Goal)
            .where(
                models.Goal.goal_id == goal_id,
                models.Goal.user_id == user_id
            )
            .values(**changes)
            .returning(models.Goal)
        )
        result = await self.db.execute(stmt)
        goal = result.scalar_one_or_none()
        if goal is None:
            raise exceptions.GoalNotFoundError("Goal not found")
        return goal
    
    async def update_status(self, goal_id: UUID, new_status: str) -> None:
        """Атомарно обновляет статус цели."""
        stmt = (
            update(models.Goal)
            .where(models.Goal.goal_id == goal_id)
            .values(status=new_status, updated_at=datetime.now(timezone.utc))
        )
        await self.db.execute(stmt)

    async def get_expired_goals_batch(
        self,
        today: date,
        limit: int = 100,
        last_id: UUID | None = None
    ) -> list[models.Goal]:
        """Возвращает просроченные цели."""
        query = (
            select(models.Goal)
            .where(
                models.Goal.status == schemas.GoalStatus.ONGOING.value,
                models.Goal.finish_date < today
            )
            .order_by(models.Goal.goal_id.asc())
            .limit(limit)
        )
        if last_id:
            query = query.where(models.Goal.goal_id > last_id)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def mark_achieved_if_eligible(self, user_id: UUID, goal_id: UUID) -> models.Goal | None:
        """Атомарно переводит цель в ACHIEVED."""
        stmt = (
            update(models.Goal)
            .where(
                models.Goal.goal_id == goal_id,
                models.Goal.user_id == user_id,
                models.Goal.status == schemas.GoalStatus.ONGOING.value,
                models.Goal.current_value >= models.Goal.target_value
            )
            .values(status=schemas.GoalStatus.ACHIEVED.value, updated_at=datetime.now(timezone.utc))
            .returning(models.Goal)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_approaching_goals_batch(
        self, today: date, limit: int = 100, days_notice: int = 7
    ) -> list[models.Goal]:
        """Возвращает приближающиеся цели, не проверявшиеся 24 часа."""
        seven_days_from_now = today + timedelta(days=days_notice)
        one_day_ago = datetime.now(timezone.utc) - timedelta(days=1)
        query = (
            select(models.Goal)
            .where(
                models.Goal.status == schemas.GoalStatus.ONGOING.value,
                models.Goal.finish_date <= seven_days_from_now,
                models.Goal.finish_date >= today,
                or_(
                    models.Goal.last_checked_date == None,
                    models.Goal.last_checked_date < one_day_ago
                )
            )
            .order_by(models.Goal.finish_date.asc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def update_last_checked(self, goals_ids: list[UUID]) -> None:
        """Обновляет дату последней проверки."""
        if not goals_ids:
            return
        stmt = (
            update(models.Goal)
            .where(models.Goal.goal_id.in_(goals_ids))
            .values(last_checked_date=datetime.now(timezone.utc))
        )
        await self.db.execute(stmt)

    async def get_pending_outbox_events(self, limit: int = 100) -> list[models.OutboxEvent]:
        """Получает события для отправки с блокировкой."""
        query = (
            select(models.OutboxEvent)
            .where(models.OutboxEvent.status == 'pending')
            .order_by(models.OutboxEvent.created_at.asc())
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def delete_outbox_events(self, event_ids: list[UUID]) -> None:
        """Удаляет отправленные события."""
        if not event_ids:
            return
        stmt = delete(models.OutboxEvent).where(models.OutboxEvent.event_id.in_(event_ids))
        await self.db.execute(stmt)
    
    async def clean_old_processed_transactions(self, days: int = 30) -> int:
        """Удаляет ID обработанных транзакций старше days дней."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        stmt = delete(models.ProcessedTransaction).where(
            models.ProcessedTransaction.created_at < cutoff_date
        )
        result = await self.db.execute(stmt)
        return result.rowcount
    
    async def bulk_add_outbox_events(self, events: list[dict]) -> None:
        """Массовая вставка событий в Outbox."""
        if not events:
            return
            
        clean_events = []
        for event_data in events:
            try:
                topic = event_data.get("topic")
                payload = event_data.get("payload")
                event_type = payload.get("event_type", "unknown")
                
                clean_payload = serialization.recursive_normalize(payload)
                
                clean_events.append({
                    "topic": topic,
                    "event_type": event_type,
                    "payload": clean_payload,
                    "status": "pending",
                    "retry_count": 0
                })
            except Exception as e:
                logger.error(f"Bulk serialization error: {e}")
                continue

        if clean_events:
            stmt = insert(models.OutboxEvent).values(clean_events)
            await self.db.execute(stmt)

    async def bulk_update_status(self, goal_ids: list[UUID], new_status: str) -> None:
        """Массовое обновление статусов."""
        if not goal_ids:
            return
        stmt = (
            update(models.Goal)
            .where(models.Goal.goal_id.in_(goal_ids))
            .values(status=new_status, updated_at=datetime.now(timezone.utc))
        )
        await self.db.execute(stmt)