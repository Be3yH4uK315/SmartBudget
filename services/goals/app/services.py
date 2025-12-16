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
        repo: repositories.GoalRepository,
    ):
        self.repo = repo

    async def createGoal(
        self, 
        userId: UUID, 
        req: schemas.CreateGoalRequest
    ) -> models.Goal:
        """Создание цели с использованием Outbox."""
        goalId = uuid4()
        new_goal = models.Goal(
            goalId=goalId,
            userId=userId,
            name=req.name,
            targetValue=req.targetValue,
            currentValue=Decimal(0),
            finishDate=req.finishDate,
            status=models.GoalStatus.ONGOING.value
        )
        
        goal = await self.repo.create(new_goal)
        
        event = {
            "event": "goal.created",
            "goalId": str(goal.goalId),
            "userId": str(userId),
            "name": goal.name,
            "targetValue": goal.targetValue,
            "finishDate": goal.finishDate
        }

        await self.repo.addOutboxEvent(
            topic=settings.settings.KAFKA.KAFKA_TOPIC_BUDGET_EVENTS,
            event_data=event
        )
        await self.repo.db.commit()
        await self.repo.db.refresh(goal)
        
        return goal

    async def getGoalDetails(
        self, 
        userId: UUID, 
        goalId: UUID
    ) -> tuple[models.Goal, int]:
        """Логика получения 1 цели."""
        goal = await self.repo.getById(userId, goalId)
        if not goal:
            raise exceptions.GoalNotFoundError("Goal not found")

        today = datetime.now(timezone.utc).date()
        daysLeft = max((goal.finishDate - today).days, 0)
        return goal, daysLeft

    async def getMainGoals(self, userId: UUID) -> list[models.Goal]:
        """Логика получения целей для гл. экрана."""
        return await self.repo.getMainGoals(userId)

    async def getAllGoals(self, userId: UUID) -> list[models.Goal]:
        """Логика получения всех целей."""
        return await self.repo.getAllGoals(userId)

    async def updateGoal(
        self, 
        userId: UUID, 
        goalId: UUID, 
        req: schemas.GoalPatchRequest
    ) -> tuple[models.Goal, int]:
        """Логика обновления цели."""
        goal = await self.repo.getById(userId, goalId)
        if not goal:
            raise exceptions.GoalNotFoundError("Goal not found")

        changes_for_db = {}
        changes_for_kafka = {}
        update_data = req.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if value is None:
                continue
            
            if field == 'status':
                changes_for_db[field] = value.value if isinstance(value, models.GoalStatus) else value
            else:
                changes_for_db[field] = value

            val_kafka = value.value if isinstance(value, models.GoalStatus) else value
            changes_for_kafka[field] = val_kafka
        
        if not changes_for_db:
             today = datetime.now(timezone.utc).date()
             daysLeft = max((goal.finishDate - today).days, 0)
             return goal, daysLeft

        goal = await self.repo.updateFields(userId, goalId, changes_for_db)

        await self._checkAndProcessAchievement(goal)

        if changes_for_kafka:
            event_changed = {
                "event": "goal.changed", 
                "goalId": str(goalId), 
                "changes": changes_for_kafka
            }
            await self.repo.addOutboxEvent(
                topic=settings.settings.KAFKA.KAFKA_TOPIC_BUDGET_EVENTS,
                event_data=event_changed
            )

        await self.repo.db.commit()

        today = datetime.now(timezone.utc).date()
        daysLeft = max((goal.finishDate - today).days, 0)
        return goal, daysLeft

    async def updateGoalBalance(self, event: schemas.TransactionEvent):
        """Логика консьюмера."""
        amount = event.amount if event.direction == 'income' else -event.amount
        
        goal = await self.repo.adjustBalance(
            event.userId, 
            event.accountId, 
            amount, 
            event.transactionId
        )

        if goal is None:
            logger.info(f"Transaction {event.transactionId} duplicate. Checking state.")
            goal = await self.repo.getGoalByTransactionId(event.transactionId)
            if not goal:
                return
            return

        event_updated = {
            "event": "goal.updated", 
            "goalId": str(goal.goalId), 
            "currentValue": goal.currentValue,
            "status": goal.status
        }
        await self.repo.addOutboxEvent(
            topic=settings.settings.KAFKA.KAFKA_TOPIC_BUDGET_EVENTS,
            event_data=event_updated
        )

        await self._checkAndProcessAchievement(goal)
        await self.repo.db.commit()

    async def _checkAndProcessAchievement(self, goal: models.Goal) -> bool:
        """Внутренний метод, не делает коммит сам, только добавляет в сессию."""
        achieved_goal = await self.repo.markAchievedIfEligible(goal.userId, goal.goalId)
        
        if achieved_goal:
            goal.status = achieved_goal.status
            event_notif = {
                "event": "goal.alert", 
                "goalId": str(goal.goalId), 
                "type": "achieved"
            }
            await self.repo.addOutboxEvent(
                topic=settings.settings.KAFKA.KAFKA_TOPIC_BUDGET_NOTIFICATION,
                event_data=event_notif
            )
            return True

        elif (
            goal.currentValue < goal.targetValue
            and goal.status == models.GoalStatus.ACHIEVED.value
        ):
            new_status = models.GoalStatus.ONGOING.value
            await self.repo.updateFields(
                userId=goal.userId, 
                goalId=goal.goalId, 
                changes={"status": new_status}
            )
            goal.status = new_status
            return True
            
        return False

    async def check_deadlines(self):
        """Логика крона. Переводим на Outbox."""
        logger.info("Starting daily check_goals_deadlines task...")
        today = datetime.now(timezone.utc).date()
        BATCH_SIZE = 100

        while True:
            expired_batch = await self.repo.getExpiredGoalsBatch(today, limit=BATCH_SIZE)
            if not expired_batch:
                break
            
            for goal in expired_batch:
                try:
                    event_updated = {"event": "goal.updated", "goalId": str(goal.goalId), "status": "expired"}
                    await self.repo.addOutboxEvent(settings.settings.KAFKA.KAFKA_TOPIC_BUDGET_EVENTS, event_updated)
                    
                    event_notif = {"event": "goal.expired", "goalId": str(goal.goalId), "type": "expired"}
                    await self.repo.addOutboxEvent(settings.settings.KAFKA.KAFKA_TOPIC_BUDGET_NOTIFICATION, event_notif)

                    await self.repo.updateStatus(goal.goalId, models.GoalStatus.EXPIRED.value)
                except Exception as e:
                    logger.error(f"Error processing expired {goal.goalId}: {e}")
            
            await self.repo.db.commit()

        while True:
            approaching_batch = await self.repo.getApproachingGoalsBatch(today, limit=BATCH_SIZE)
            if not approaching_batch:
                break
            
            processed_ids = []
            for goal in approaching_batch:
                daysLeft = (goal.finishDate - today).days
                event_notif = {
                    "event": "goal.approaching", 
                    "goalId": str(goal.goalId), 
                    "type": "approaching",
                    "daysLeft": daysLeft
                }
                await self.repo.addOutboxEvent(settings.settings.KAFKA.KAFKA_TOPIC_BUDGET_NOTIFICATION, event_notif)
                processed_ids.append(goal.goalId)

            if processed_ids:
                await self.repo.updateLastChecked(processed_ids)