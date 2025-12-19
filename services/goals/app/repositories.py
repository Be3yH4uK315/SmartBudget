from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import json
import logging
from uuid import UUID
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, insert, or_, select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app import models, exceptions

logger = logging.getLogger(__name__)

MAX_RETRIES = 5

def _json_serializer(obj):
    """Преобразует сложные типы в строки для сохранения в JSON column."""
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if isinstance(obj, UUID):
        return str(obj)
    raise TypeError(f"Type {type(obj)} not serializable")

class GoalRepository:
    """Репозиторий для операций с целями."""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: UUID, goal_id: UUID) -> models.Goal | None:
        """Получает цель по ID и ID пользователя."""
        try:
            result = await self.db.execute(
                select(models.Goal).where(
                    models.Goal.goal_id == goal_id,
                    models.Goal.user_id == user_id
                )
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Failed to get goal {goal_id}: {e}")
            raise exceptions.InvalidGoalDataError(f"Database error: {str(e)}")

    async def create(self, goal_model: models.Goal) -> models.Goal:
        """Создает новую цель."""
        try:
            self.db.add(goal_model)
            await self.db.flush() 
            return goal_model
        except IntegrityError as e:
            await self.db.rollback()
            logger.error(f"Integrity error creating goal: {e}")
            raise exceptions.InvalidGoalDataError("Invalid goal data")
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Database error creating goal: {e}")
            raise exceptions.InvalidGoalDataError("Database error")

    async def get_main_goals(self, user_id: UUID) -> list[models.Goal]:
        """Получает цели для главного экрана (топ 10 активных)."""
        try:
            query = (
                select(models.Goal)
                .where(
                    models.Goal.user_id == user_id,
                    models.Goal.status == models.GoalStatus.ONGOING.value
                )
                .order_by((models.Goal.target_value - models.Goal.current_value).asc())
                .limit(10)
            )
            result = await self.db.execute(query)
            return result.scalars().all()
        except SQLAlchemyError as e:
            logger.error(f"Failed to get main goals: {e}")
            return []

    async def get_all_goals(self, user_id: UUID) -> list[models.Goal]:
        """Получает все цели пользователя."""
        try:
            query = (
                select(models.Goal)
                .where(models.Goal.user_id == user_id)
                .order_by(models.Goal.finish_date.asc())
            )
            result = await self.db.execute(query)
            return result.scalars().all()
        except SQLAlchemyError as e:
            logger.error(f"Failed to get all goals: {e}")
            return []
    
    async def add_outbox_event(self, topic: str, event_data: dict) -> None:
        """Добавляет событие в Outbox."""
        try:
            event_type = event_data.get("event", "unknown")
            safe_payload = json.loads(json.dumps(event_data, default=_json_serializer))
            outbox_entry = models.OutboxEvent(
                topic=topic,
                event_type=event_type,
                payload=safe_payload,
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
        try:
            stmt = insert(models.ProcessedTransaction).values(
                transaction_id=transaction_id,
                goal_id=goal_id
            )
            await self.db.execute(stmt)
        except IntegrityError:
            await self.db.rollback()
            logger.info(f"Transaction {transaction_id} already processed")
            return None
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Failed to mark transaction as processed: {e}")
            raise

        try:
            new_value = sa.func.greatest(Decimal(0), models.Goal.current_value + amount)

            query = (
                update(models.Goal)
                .where(models.Goal.goal_id == goal_id, models.Goal.user_id == user_id)
                .values(current_value=new_value)
                .execution_options(synchronize_session=False)
                .returning(models.Goal)
            )

            result = await self.db.execute(query)
            updated_goal = result.scalar_one_or_none()

            if not updated_goal:
                await self.db.rollback()
                raise exceptions.GoalNotFoundError(f"Goal {goal_id} not found")

            return updated_goal
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Failed to adjust balance: {e}")
            raise

    async def update_fields(self, user_id: UUID, goal_id: UUID, changes: dict) -> models.Goal:
        """Обновляет переданные поля."""
        try:
            stmt = (
                update(models.Goal)
                .where(models.Goal.goal_id == goal_id, models.Goal.user_id == user_id)
                .values(**changes)
                .returning(models.Goal)
            )
            result = await self.db.execute(stmt)
            updated_goal = result.scalar_one_or_none()
            if not updated_goal:
                raise exceptions.GoalNotFoundError("Goal not found during update")
            return updated_goal
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Failed to update goal fields: {e}")
            raise exceptions.InvalidGoalDataError(f"Update failed: {str(e)}")
    
    async def update_status(self, goal_id: UUID, new_status: str) -> None:
        """Атомарно обновляет статус цели."""
        try:
            stmt = (
                update(models.Goal)
                .where(models.Goal.goal_id == goal_id)
                .values(status=new_status, updated_at=datetime.now(timezone.utc))
            )
            await self.db.execute(stmt)
        except SQLAlchemyError as e:
            logger.error(f"Failed to update goal status: {e}")
            raise

    async def get_expired_goals_batch(self, today: date, limit: int = 100) -> list[models.Goal]:
        """Возвращает просроченные цели."""
        try:
            query = (
                select(models.Goal)
                .where(
                    models.Goal.status == models.GoalStatus.ONGOING.value,
                    models.Goal.finish_date < today
                )
                .order_by(models.Goal.created_at.asc())
                .limit(limit)
            )
            result = await self.db.execute(query)
            return result.scalars().all()
        except SQLAlchemyError as e:
            logger.error(f"Failed to get expired goals: {e}")
            return []

    async def mark_achieved_if_eligible(self, user_id: UUID, goal_id: UUID) -> models.Goal | None:
        """Атомарно переводит цель в ACHIEVED."""
        try:
            stmt = (
                update(models.Goal)
                .where(
                    models.Goal.goal_id == goal_id,
                    models.Goal.user_id == user_id,
                    models.Goal.status == models.GoalStatus.ONGOING.value,
                    models.Goal.current_value >= models.Goal.target_value
                )
                .values(status=models.GoalStatus.ACHIEVED.value, updated_at=datetime.now(timezone.utc))
                .returning(models.Goal)
            )
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Failed to mark goal as achieved: {e}")
            return None

    async def get_approaching_goals_batch(
        self, 
        today: date, 
        limit: int = 100, 
        days_notice: int = 7
    ) -> list[models.Goal]:
        """Возвращает приближающиеся цели, не проверявшиеся 24 часа."""
        try:
            seven_days_from_now = today + timedelta(days=days_notice)
            one_day_ago = datetime.now(timezone.utc) - timedelta(days=1)

            query = (
                select(models.Goal)
                .where(
                    models.Goal.status == models.GoalStatus.ONGOING.value,
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
        except SQLAlchemyError as e:
            logger.error(f"Failed to get approaching goals: {e}")
            return []

    async def update_last_checked(self, goals_ids: list[UUID]) -> None:
        """Обновляет дату последней проверки."""
        if not goals_ids:
            return
        try:
            stmt = (
                update(models.Goal)
                .where(models.Goal.goal_id.in_(goals_ids))
                .values(last_checked_date=datetime.now(timezone.utc))
            )
            await self.db.execute(stmt)
        except SQLAlchemyError as e:
            logger.error(f"Failed to update last_checked_date: {e}")
    
    async def get_goal_by_transaction_id(self, transaction_id: UUID) -> models.Goal | None:
        """Находит цель по ID транзакции."""
        try:
            query = (
                select(models.Goal)
                .join(models.ProcessedTransaction, models.Goal.goal_id == models.ProcessedTransaction.goal_id)
                .where(models.ProcessedTransaction.transaction_id == transaction_id)
            )
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Failed to get goal by transaction: {e}")
            return None

    async def get_pending_outbox_events(self, limit: int = 100) -> list[models.OutboxEvent]:
        """Получает события для отправки с блокировкой."""
        try:
            query = (
                select(models.OutboxEvent)
                .where(models.OutboxEvent.status == 'pending')
                .order_by(models.OutboxEvent.created_at.asc())
                .limit(limit)
                .with_for_update(skip_locked=True)
            )
            result = await self.db.execute(query)
            return result.scalars().all()
        except SQLAlchemyError as e:
            logger.error(f"Failed to get pending outbox events: {e}")
            return []
    
    async def handle_failed_outbox_event(self, event_id: UUID, error_msg: str) -> None:
        """Обрабатывает неудачу отправки события."""
        try:
            stmt = select(models.OutboxEvent).where(models.OutboxEvent.event_id == event_id)
            result = await self.db.execute(stmt)
            event = result.scalar_one_or_none()
            
            if event:
                event.retry_count += 1
                event.last_error = error_msg[:512]
                if event.retry_count >= MAX_RETRIES:
                    event.status = 'failed'
                    logger.error(f"Event {event_id} exceeded max retries")
                self.db.add(event)
        except SQLAlchemyError as e:
            logger.error(f"Failed to handle failed outbox event: {e}")

    async def delete_outbox_events(self, event_ids: list[UUID]) -> None:
        """Удаляет отправленные события."""
        if not event_ids:
            return
        try:
            stmt = delete(models.OutboxEvent).where(models.OutboxEvent.event_id.in_(event_ids))
            await self.db.execute(stmt)
        except SQLAlchemyError as e:
            logger.error(f"Failed to delete outbox events: {e}")