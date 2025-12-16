import logging
from uuid import UUID, uuid4
from decimal import Decimal
from datetime import date, datetime, timezone
import asyncio

from app import (
    models, 
    repositories, 
    exceptions, 
    schemas
)
from app.kafka_producer import KafkaProducer

logger = logging.getLogger(__name__)

class GoalService:
    def __init__(
        self,
        repo: repositories.GoalRepository,
        kafka: KafkaProducer
    ):
        self.repo = repo
        self.kafka = kafka

    async def create_goal(
        self, 
        user_id: UUID, 
        req: schemas.CreateGoalRequest
    ) -> models.Goal:
        """Логика создания цели."""
        goal_id = uuid4()
        new_goal = models.Goal(
            id=goal_id,
            user_id=user_id,
            name=req.name,
            target_value=req.target_value,
            current_value=Decimal(0),
            finish_date=req.finish_date,
            status=models.GoalStatus.IN_PROGRESS.value
        )
        
        goal = await self.repo.create(new_goal)
        
        event = {
            "event": "goal.created",
            "goal_id": str(goal.id),
            "user_id": str(user_id),
            "name": goal.name,
            "target_value": goal.target_value,
            "finish_date": goal.finish_date.isoformat()
        }
        await self.kafka.send_budget_event(event)
        
        return goal

    async def get_goal_details(
        self, 
        user_id: UUID, 
        goal_id: UUID
    ) -> tuple[models.Goal, int]:
        """Логика получения 1 цели."""
        goal = await self.repo.get_by_id(user_id, goal_id)
        if not goal:
            raise exceptions.GoalNotFoundError("Goal not found")

        today = datetime.now(timezone.utc).date()
        days_left = max((goal.finish_date - today).days, 0)
        
        return goal, days_left

    async def get_main_goals(self, user_id: UUID) -> list[models.Goal]:
        """Логика получения целей для гл. экрана."""
        return await self.repo.get_main_goals(user_id)

    async def get_all_goals(self, user_id: UUID) -> list[models.Goal]:
        """Логика получения всех целей."""
        return await self.repo.get_all_goals(user_id)

    async def update_goal(
        self, 
        user_id: UUID, 
        goal_id: UUID, 
        req: schemas.GoalPatchRequest
    ) -> tuple[models.Goal, int]:
        """Логика обновления цели."""
        goal = await self.repo.get_by_id(user_id, goal_id)
        if not goal:
            raise exceptions.GoalNotFoundError("Goal not found")

        changes_for_db = {}
        changes_for_kafka = {}
        update_data = req.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if value is None:
                continue
            
            if field == 'status':
                try:
                    status_enum = models.GoalStatus(value)
                    changes_for_db[field] = status_enum.value
                except ValueError:
                    raise exceptions.InvalidGoalDataError(f"Invalid status: {value}")
            else:
                changes_for_db[field] = value
            
            changes_for_kafka[field] = value if not isinstance(value, date) else value.isoformat()
        
        if not changes_for_db:
             today = datetime.now(timezone.utc).date()
             days_left = max((goal.finish_date - today).days, 0)
             return goal, days_left

        goal = await self.repo.update_fields(user_id, goal_id, changes_for_db)

        await self._check_and_process_achievement(goal)

        if changes_for_kafka:
            event_changed = {"event": "goal.changed", "goal_id": str(goal_id), "changes": changes_for_kafka}
            await self.kafka.send_budget_event(event_changed)

        today = datetime.now(timezone.utc).date()
        days_left = max((goal.finish_date - today).days, 0)
            
        return goal, days_left

    async def update_goal_balance(self, event: schemas.TransactionEvent):
        """Логика консьюмера."""
        amount = event.amount if event.direction == 'income' else -event.amount
        
        goal = await self.repo.adjust_balance(
            event.user_id, 
            event.account_id, 
            amount, 
            event.transaction_id
        )

        if goal is None:
            logger.info(f"Transaction {event.transaction_id} already processed. Skipping.")
            return
        
        event_updated = {
            "event": "goal.updated", 
            "goal_id": str(goal.id), 
            "current_value": goal.current_value,
            "status": goal.status
        }
        await self.kafka.send_budget_event(event_updated)

        await self._check_and_process_achievement(goal)

    async def _check_and_process_achievement(self, goal: models.Goal) -> bool:
        """
        Проверяет, достигнута ли цель.
        Использует атомарный update в БД, чтобы избежать двойных уведомлений.
        """
        achieved_goal = await self.repo.mark_achieved_if_eligible(goal.user_id, goal.id)
        
        if achieved_goal:
            goal.status = achieved_goal.status
            
            event_notif = {
                "event": "goal.alert", 
                "goal_id": str(goal.id), 
                "type": "achieved"
            }
            await self.kafka.send_notification(event_notif)
            return True

        elif (
            goal.current_value < goal.target_value
            and goal.status == models.GoalStatus.ACHIEVED.value
        ):
            new_status = models.GoalStatus.IN_PROGRESS.value
            await self.repo.update_fields(
                user_id=goal.user_id, 
                goal_id=goal.id, 
                changes={"status": new_status}
            )
            goal.status = new_status
            return True
            
        return False

    async def check_deadlines(self):
        """
        Логика Arq воркера с защитой от переполнения памяти (Batching).
        """
        logger.info("Starting daily check_goals_deadlines task...")
        today = datetime.now(timezone.utc).date()
        BATCH_SIZE = 100
        
        total_expired = 0
        while True:
            expired_batch = await self.repo.get_expired_goals_batch(today, limit=BATCH_SIZE)
            if not expired_batch:
                break
            
            kafka_tasks = []
            
            for goal in expired_batch:
                goal.status = models.GoalStatus.EXPIRED.value
                
                event_updated = {
                    "event": "goal.updated", 
                    "goal_id": str(goal.id), 
                    "status": "expired"
                }
                kafka_tasks.append(self.kafka.send_budget_event(event_updated))
                
                event_notif = {
                    "event": "goal.expired", 
                    "goal_id": str(goal.id), 
                    "type": "expired"
                }
                kafka_tasks.append(self.kafka.send_notification(event_notif))
            
            await self.repo.update_bulk(expired_batch)
            
            if kafka_tasks:
                results = await asyncio.gather(*kafka_tasks, return_exceptions=True)
            
            total_expired += len(expired_batch)
            logger.info(f"Processed batch of {len(expired_batch)} expired goals.")

        logger.info(f"Finished expired goals. Total processed: {total_expired}")

        total_approaching = 0
        while True:
            approaching_batch = await self.repo.get_approaching_goals_batch(today, limit=BATCH_SIZE, days_notice=7)
            
            if not approaching_batch:
                break
            
            kafka_tasks = []
            
            for goal in approaching_batch:
                days_left = (goal.finish_date - today).days
                goal.last_checked_date = datetime.now(timezone.utc)
                
                event_notif = {
                    "event": "goal.approaching", 
                    "goal_id": str(goal.id), 
                    "type": "approaching",
                    "days_left": days_left
                }
                kafka_tasks.append(self.kafka.send_notification(event_notif))

            await self.repo.update_bulk(approaching_batch)
            
            if kafka_tasks:
                await asyncio.gather(*kafka_tasks, return_exceptions=True)
                
            total_approaching += len(approaching_batch)
            logger.info(f"Processed batch of {len(approaching_batch)} approaching goals.")

        logger.info(
            f"Job finished. Total Expired: {total_expired}, Total Approaching: {total_approaching}"
        )