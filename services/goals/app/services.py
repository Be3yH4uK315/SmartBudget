import logging
from uuid import UUID, uuid4
from decimal import Decimal
from datetime import datetime, timezone

from app import (
    models, 
    repositories, 
    exceptions, 
    schemas,
    settings
)

logger = logging.getLogger(__name__)

class GoalService:
    def __init__(
        self,
        repository: repositories.GoalRepository,
    ):
        self.repository = repository

    async def createGoal(
        self, 
        userId: UUID, 
        request: schemas.CreateGoalRequest
    ) -> models.Goal:
        """Создание цели с использованием Outbox."""
        goalId = uuid4()
        newGoal = models.Goal(
            goalId=goalId,
            userId=userId,
            name=request.name,
            targetValue=request.targetValue,
            currentValue=Decimal(0),
            finishDate=request.finishDate,
            status=models.GoalStatus.ONGOING.value
        )
        
        goal = await self.repository.create(newGoal)
        
        event = {
            "event": "goal.created",
            "goalId": str(goal.goalId),
            "userId": str(userId),
            "name": goal.name,
            "targetValue": goal.targetValue,
            "finishDate": goal.finishDate
        }

        await self.repository.addOutboxEvent(
            topic=settings.settings.KAFKA.KAFKA_TOPIC_BUDGET_EVENTS,
            eventData=event
        )
        await self.repository.db.commit()
        await self.repository.db.refresh(goal)
        
        return goal

    async def getGoalDetails(
        self, 
        userId: UUID, 
        goalId: UUID
    ) -> tuple[models.Goal, int]:
        """Логика получения 1 цели."""
        goal = await self.repository.getById(userId, goalId)
        if not goal:
            raise exceptions.GoalNotFoundError("Goal not found")

        today = datetime.now(timezone.utc).date()
        daysLeft = max((goal.finishDate - today).days, 0)
        return goal, daysLeft

    async def getMainGoals(self, userId: UUID) -> list[models.Goal]:
        """Логика получения целей для гл. экрана."""
        return await self.repository.getMainGoals(userId)

    async def getAllGoals(self, userId: UUID) -> list[models.Goal]:
        """Логика получения всех целей."""
        return await self.repository.getAllGoals(userId)

    async def updateGoal(
        self, 
        userId: UUID, 
        goalId: UUID, 
        request: schemas.GoalPatchRequest
    ) -> tuple[models.Goal, int]:
        """Логика обновления цели."""
        goal = await self.repository.getById(userId, goalId)
        if not goal:
            raise exceptions.GoalNotFoundError("Goal not found")

        changesForDb = {}
        changesForKafka = {}
        updateData = request.model_dump(exclude_unset=True)

        for field, value in updateData.items():
            if value is None:
                continue
            
            if field == 'status':
                changesForDb[field] = value.value if isinstance(value, models.GoalStatus) else value
            else:
                changesForDb[field] = value

            valueKafka = value.value if isinstance(value, models.GoalStatus) else value
            changesForKafka[field] = valueKafka
        
        if not changesForDb:
             today = datetime.now(timezone.utc).date()
             daysLeft = max((goal.finishDate - today).days, 0)
             return goal, daysLeft

        goal = await self.repository.updateFields(userId, goalId, changesForDb)

        await self._checkAndProcessAchievement(goal)

        if changesForKafka:
            eventChanged = {
                "event": "goal.changed", 
                "goalId": str(goalId), 
                "changes": changesForKafka
            }
            await self.repository.addOutboxEvent(
                topic=settings.settings.KAFKA.KAFKA_TOPIC_BUDGET_EVENTS,
                eventData=eventChanged
            )

        await self.repository.db.commit()

        today = datetime.now(timezone.utc).date()
        daysLeft = max((goal.finishDate - today).days, 0)
        return goal, daysLeft

    async def updateGoalBalance(self, event: schemas.TransactionEvent):
        """Логика консьюмера."""
        value = event.value * (1 if event.type is schemas.TransactionType.INCOME else -1)
        
        goal = await self.repository.adjustBalance(
            event.userId, 
            event.accountId, 
            value, 
            event.transactionId
        )

        if goal is None:
            logger.info(f"Transaction {event.transactionId} duplicate. Checking state.")
            goal = await self.repository.getGoalByTransactionId(event.transactionId)
            if not goal:
                return
            return

        eventUpdated = {
            "event": "goal.updated", 
            "goalId": str(goal.goalId), 
            "currentValue": goal.currentValue,
            "status": goal.status
        }
        await self.repository.addOutboxEvent(
            topic=settings.settings.KAFKA.KAFKA_TOPIC_BUDGET_EVENTS,
            eventData=eventUpdated
        )

        await self._checkAndProcessAchievement(goal)
        await self.repository.db.commit()

    async def _checkAndProcessAchievement(self, goal: models.Goal) -> bool:
        """Внутренний метод, не делает коммит сам, только добавляет в сессию."""
        achievedGoal = await self.repository.markAchievedIfEligible(goal.userId, goal.goalId)
        
        if achievedGoal:
            goal.status = achievedGoal.status
            eventNotif = {
                "event": "goal.alert", 
                "goalId": str(goal.goalId), 
                "type": "achieved"
            }
            await self.repository.addOutboxEvent(
                topic=settings.settings.KAFKA.KAFKA_TOPIC_BUDGET_NOTIFICATION,
                eventData=eventNotif
            )
            return True

        elif (
            goal.currentValue < goal.targetValue
            and goal.status == models.GoalStatus.ACHIEVED.value
        ):
            newStatus = models.GoalStatus.ONGOING.value
            await self.repository.updateFields(
                userId=goal.userId, 
                goalId=goal.goalId, 
                changes={"status": newStatus}
            )
            goal.status = newStatus
            return True
            
        return False

    async def check_deadlines(self):
        """Логика крона. Переводим на Outbox."""
        logger.info("Starting daily check_goals_deadlines task...")
        today = datetime.now(timezone.utc).date()
        BATCH_SIZE = 100

        while True:
            expiredBatch = await self.repository.getExpiredGoalsBatch(today, limit=BATCH_SIZE)
            if not expiredBatch:
                break
            
            for goal in expiredBatch:
                try:
                    eventUpdated = {"event": "goal.updated", "goalId": str(goal.goalId), "status": "expired"}
                    await self.repository.addOutboxEvent(settings.settings.KAFKA.KAFKA_TOPIC_BUDGET_EVENTS, eventUpdated)
                    
                    eventNotif = {"event": "goal.expired", "goalId": str(goal.goalId), "type": "expired"}
                    await self.repository.addOutboxEvent(settings.settings.KAFKA.KAFKA_TOPIC_BUDGET_NOTIFICATION, eventNotif)

                    await self.repository.updateStatus(goal.goalId, models.GoalStatus.EXPIRED.value)
                except Exception as e:
                    logger.error(f"Error processing expired {goal.goalId}: {e}")
            
            await self.repository.db.commit()

        while True:
            approachingBatch = await self.repository.getApproachingGoalsBatch(today, limit=BATCH_SIZE)
            if not approachingBatch:
                break
            
            processedIds = []
            for goal in approachingBatch:
                daysLeft = (goal.finishDate - today).days
                eventNotif = {
                    "event": "goal.approaching", 
                    "goalId": str(goal.goalId), 
                    "type": "approaching",
                    "daysLeft": daysLeft
                }
                await self.repository.addOutboxEvent(settings.settings.KAFKA.KAFKA_TOPIC_BUDGET_NOTIFICATION, eventNotif)
                processedIds.append(goal.goalId)

            if processedIds:
                await self.repository.updateLastChecked(processedIds)