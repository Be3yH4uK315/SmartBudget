from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import json
import logging
from uuid import UUID
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, insert, or_, select, update
from sqlalchemy.exc import IntegrityError

from app import models, exceptions

logger = logging.getLogger(__name__)

def _jsonSerializer(obj):
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

    async def getById(self, userId: UUID, goalId: UUID) -> models.Goal | None:
        """Получает цель по ID и ID пользователя."""
        result = await self.db.execute(
            select(models.Goal).where(
                models.Goal.goalId == goalId,
                models.Goal.userId == userId
            )
        )
        return result.scalar_one_or_none()

    async def create(self, goalModel: models.Goal) -> models.Goal:
        """Создает новую цель."""
        try:
            self.db.add(goalModel)
            await self.db.flush() 
            return goalModel
        except IntegrityError as e:
            logger.error(f"DATABASE INTEGRITY ERROR: {e}")
            await self.db.rollback()
            raise exceptions.InvalidGoalDataError(f"Goal creation failed: {e.orig}")

    async def getMainGoals(self, userId: UUID) -> list[models.Goal]:
        """Получает цели для главного экрана."""
        query = (
            select(models.Goal)
            .where(
                models.Goal.userId == userId,
                models.Goal.status == models.GoalStatus.ONGOING.value
            )
            .order_by((models.Goal.targetValue - models.Goal.currentValue).asc())
            .limit(10)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def getAllGoals(self, userId: UUID) -> list[models.Goal]:
        """Получает все цели пользователя."""
        query = (
            select(models.Goal)
            .where(models.Goal.userId == userId)
            .order_by(models.Goal.finishDate.asc())
        )
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def addOutboxEvent(self, topic: str, eventData: dict):
        """Добавляет событие в Outbox."""
        eventType = eventData.get("event", "unknown")
        safePayload = json.loads(json.dumps(eventData, default=_jsonSerializer))
        outbox_entry = models.OutboxEvent(
            topic=topic,
            eventType=eventType,
            payload=safePayload
        )
        self.db.add(outbox_entry)

    async def adjustBalance(
        self, userId: UUID, 
        goalId: UUID, 
        amount: Decimal, 
        transactionId: UUID
    ) -> models.Goal | None:
        """Атомарно изменяет баланс цели."""
        try:
            stmt = insert(models.ProcessedTransaction).values(
                transactionId=transactionId,
                goalId=goalId
            )
            await self.db.execute(stmt)
        except IntegrityError:
            await self.db.rollback()
            return None

        newValue = sa.func.greatest(0, models.Goal.currentValue + amount)

        query = (
            update(models.Goal)
            .where(models.Goal.goalId == goalId, models.Goal.userId == userId)
            .values(currentValue=newValue)
            .execution_options(synchronize_session=False)
            .returning(models.Goal)
        )

        result = await self.db.execute(query)
        updatedGoal = result.scalar_one_or_none()

        if not updatedGoal:
            await self.db.rollback()
            raise exceptions.GoalNotFoundError(f"Goal {goalId} not found")

        return updatedGoal

    async def updateFields(self, userId: UUID, goalId: UUID, changes: dict) -> models.Goal:
        """
        Обновляет переданные поля, чтобы не затереть баланс.
        """
        stmt = (
            update(models.Goal)
            .where(models.Goal.goalId == goalId, models.Goal.userId == userId)
            .values(**changes)
            .returning(models.Goal)
        )
        result = await self.db.execute(stmt)
        updatedGoal = result.scalar_one_or_none()
        if not updatedGoal:
             raise exceptions.GoalNotFoundError("Goal not found during update")
        return updatedGoal
    
    async def updateStatus(self, goalId: UUID, new_status: str):
        """Метод для атомарного обновления статуса (для воркера)."""
        stmt = (
            update(models.Goal)
            .where(models.Goal.goalId == goalId)
            .values(status=new_status)
        )
        await self.db.execute(stmt)

    async def getExpiredGoalsBatch(self, today: date, limit: int = 100) -> list[models.Goal]:
        """Возвращает пачку целей, которые просрочены и все еще ONGOING."""
        query = (
            select(models.Goal)
            .where(
                models.Goal.status == models.GoalStatus.ONGOING.value,
                models.Goal.finishDate < today
            )
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def markAchievedIfEligible(self, userId: UUID, goalId: UUID) -> models.Goal | None:
        """
        Атомарно переводит цель в ACHIEVED, только если она выполнена 
        и еще находится в ONGOING.
        """
        stmt = (
            update(models.Goal)
            .where(
                models.Goal.goalId == goalId,
                models.Goal.userId == userId,
                models.Goal.status == models.GoalStatus.ONGOING.value,
                models.Goal.currentValue >= models.Goal.targetValue
            )
            .values(status=models.GoalStatus.ACHIEVED.value)
            .returning(models.Goal)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def getApproachingGoalsBatch(
        self, 
        today: date, 
        limit: int = 100, 
        daysNotice: int = 7
    ) -> list[models.Goal]:
        """
        Возвращает пачку целей, у которых скоро дедлайн и которые 
        НЕ проверялись за последние 24 часа.
        """
        sevenDaysFromNow = today + timedelta(days=daysNotice)
        oneDayAgo = datetime.now(timezone.utc) - timedelta(days=1)

        query = (
            select(models.Goal)
            .where(
                models.Goal.status == models.GoalStatus.ONGOING.value,
                models.Goal.finishDate <= sevenDaysFromNow,
                models.Goal.finishDate >= today,
                or_(
                    models.Goal.lastCheckedDate == None,
                    models.Goal.lastCheckedDate < oneDayAgo
                )
            )
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def updateLastChecked(self, goalsIds: list[UUID]):
        """Обновляем дату проверки, чтобы не спамить уведомлениями."""
        if not goalsIds:
            return
        stmt = (
            update(models.Goal)
            .where(models.Goal.goalId.in_(goalsIds))
            .values(lastCheckedDate=datetime.now(timezone.utc))
        )
        await self.db.execute(stmt)
        await self.db.commit()
    
    async def getGoalByTransactionId(self, transactionId: UUID) -> models.Goal | None:
        """Находит цель, связанную с уже обработанной транзакцией."""
        query = (
            select(models.Goal)
            .join(models.ProcessedTransaction, models.Goal.goalId == models.ProcessedTransaction.goalId)
            .where(models.ProcessedTransaction.transactionId == transactionId)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def getPendingOutboxEvents(self, limit: int = 100) -> list[models.OutboxEvent]:
        """Получает пачку событий для отправки с блокировкой строк."""
        query = (
            select(models.OutboxEvent)
            .where(models.OutboxEvent.status == 'pending')
            .order_by(models.OutboxEvent.createdAt.asc())
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def handleFailedOutboxEvent(self, eventId: UUID, errorMsg: str):
        """
        Увеличивает счетчик попыток. Если > 5, помечает как failed.
        """
        stmt = select(models.OutboxEvent).where(models.OutboxEvent.eventId == eventId)
        result = await self.db.execute(stmt)
        event = result.scalar_one_or_none()
        
        if event:
            event.retryСount += 1
            if event.retryСount >= 5:
                event.status = 'failed'
                
            self.db.add(event)

    async def deleteOutboxEvents(self, eventIds: list[UUID]):
        """Удаляет успешно отправленные события."""
        if not eventIds:
            return
        stmt = delete(models.OutboxEvent).where(models.OutboxEvent.eventId.in_(eventIds))
        await self.db.execute(stmt)