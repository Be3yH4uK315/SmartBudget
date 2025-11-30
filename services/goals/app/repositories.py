from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
import sqlalchemy as sa
from decimal import Decimal

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
    
    async def update(self, goal: models.Goal) -> models.Goal:
        """Сохраняет изменения в цели."""
        await self.db.commit()
        await self.db.refresh(goal)
        return goal
        
    async def get_goals_for_check(self) -> list[models.Goal]:
        """Выбирает цели для фоновой проверки."""
        query = select(models.Goal).where(
            models.Goal.status == models.GoalStatus.IN_PROGRESS.value
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def update_bulk(self, goals: list[models.Goal]):
        """Массово коммитит изменения (для воркера)."""
        await self.db.commit()