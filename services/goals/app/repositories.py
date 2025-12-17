from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, or_, select, update
from sqlalchemy.exc import IntegrityError

from app import models, exceptions

class GoalRepository:
    """Репозиторий для операций с целями."""
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: UUID, goal_id: UUID) -> models.Goal | None:
        """Получает цель по ID и ID пользователя."""
        result = await self.db.execute(
            select(models.Goal).where(
                models.Goal.id == goal_id,
                models.Goal.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def create(self, goal_model: models.Goal) -> models.Goal:
        """Создает новую цель."""
        try:
            self.db.add(goal_model)
            await self.db.commit()
            await self.db.refresh(goal_model)
            return goal_model
        except IntegrityError:
            await self.db.rollback()
            raise exceptions.InvalidGoalDataError("Goal creation failed")

    async def get_main_goals(self, user_id: UUID) -> list[models.Goal]:
        """Получает цели для главного экрана."""
        query = (
            select(models.Goal)
            .where(
                models.Goal.user_id == user_id,
                models.Goal.status == models.GoalStatus.IN_PROGRESS.value
            )
            .order_by((models.Goal.target_value - models.Goal.current_value).asc())
            .limit(10)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_all_goals(self, user_id: UUID) -> list[models.Goal]:
        """Получает все цели пользователя."""
        query = (
            select(models.Goal)
            .where(models.Goal.user_id == user_id)
            .order_by(models.Goal.finish_date.asc())
        )
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def adjust_balance(
        self, user_id: UUID, 
        goal_id: UUID, 
        amount: Decimal, 
        transaction_id: UUID
    ) -> models.Goal | None:
        """Атомарно изменяет баланс цели."""
        try:
            stmt = insert(models.ProcessedTransaction).values(
                transaction_id=transaction_id,
                goal_id=goal_id
            )
            await self.db.execute(stmt)
        except IntegrityError:
            await self.db.rollback()
            return None

        new_value_expr = sa.func.greatest(0, models.Goal.current_value + amount)

        query = (
            update(models.Goal)
            .where(models.Goal.id == goal_id, models.Goal.user_id == user_id)
            .values(current_value=new_value_expr)
            .execution_options(synchronize_session="fetch")
            .returning(models.Goal)
        )

        result = await self.db.execute(query)
        updated_goal = result.scalar_one_or_none()

        if not updated_goal:
            await self.db.rollback()
            raise exceptions.GoalNotFoundError(f"Goal {goal_id} not found")

        await self.db.commit()
        return updated_goal

    async def update_fields(self, user_id: UUID, goal_id: UUID, changes: dict) -> models.Goal:
        """
        Обновляет переданные поля, чтобы не затереть баланс.
        """
        stmt = (
            update(models.Goal)
            .where(models.Goal.id == goal_id, models.Goal.user_id == user_id)
            .values(**changes)
            .returning(models.Goal)
        )
        result = await self.db.execute(stmt)
        updated_goal = result.scalar_one_or_none()
        
        if not updated_goal:
             raise exceptions.GoalNotFoundError("Goal not found during update")
             
        await self.db.commit()
        return updated_goal
        
    async def get_expired_goals_batch(self, today: date, limit: int = 100) -> list[models.Goal]:
        """Возвращает пачку целей, которые просрочены и все еще IN_PROGRESS."""
        query = (
            select(models.Goal)
            .where(
                models.Goal.status == models.GoalStatus.IN_PROGRESS.value,
                models.Goal.finish_date < today
            )
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def mark_achieved_if_eligible(self, user_id: UUID, goal_id: UUID) -> models.Goal | None:
        """
        Атомарно переводит цель в ACHIEVED, только если она выполнена 
        и еще находится в IN_PROGRESS.
        """
        stmt = (
            update(models.Goal)
            .where(
                models.Goal.id == goal_id,
                models.Goal.user_id == user_id,
                models.Goal.status == models.GoalStatus.IN_PROGRESS.value,
                models.Goal.current_value >= models.Goal.target_value
            )
            .values(status=models.GoalStatus.ACHIEVED.value)
            .returning(models.Goal)
        )
        
        result = await self.db.execute(stmt)
        updated_goal = result.scalar_one_or_none()
        
        if updated_goal:
            await self.db.commit()
            
        return updated_goal

    async def get_approaching_goals_batch(
        self, 
        today: date, 
        limit: int = 100, 
        days_notice: int = 7
    ) -> list[models.Goal]:
        """
        Возвращает пачку целей, у которых скоро дедлайн и которые 
        НЕ проверялись за последние 24 часа.
        """
        seven_days_from_now = today + timedelta(days=days_notice)
        one_day_ago = datetime.now(timezone.utc) - timedelta(days=1)

        query = (
            select(models.Goal)
            .where(
                models.Goal.status == models.GoalStatus.IN_PROGRESS.value,
                models.Goal.finish_date <= seven_days_from_now,
                models.Goal.finish_date >= today,
                or_(
                    models.Goal.last_checked_date == None,
                    models.Goal.last_checked_date < one_day_ago
                )
            )
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def update_bulk(self, goals: list[models.Goal]):
        """Массово коммитит изменения (для воркера)."""
        try:
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise