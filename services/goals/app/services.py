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

    async def create_goal(
        self, 
        user_id: UUID, 
        req: schemas.CreateGoalRequest
    ) -> models.Goal:
        """Создание цели с использованием Outbox."""
        goal_id = uuid4()
        new_goal = models.Goal(
            id=goal_id,
            user_id=user_id,
            name=req.name,
            target_value=req.target_value,
            current_value=Decimal(0),
            finish_date=req.finish_date,
            status=models.GoalStatus.ONGOING.value
        )
        
        goal = await self.repo.create(new_goal)
        
        event = {
            "event": "goal.created",
            "goal_id": str(goal.id),
            "user_id": str(user_id),
            "name": goal.name,
            "target_value": goal.target_value,
            "finish_date": goal.finish_date
        }

        await self.repo.add_outbox_event(
            topic=settings.settings.kafka.kafka_topic_budget_events,
            event_data=event
        )
        await self.repo.db.commit()
        await self.repo.db.refresh(goal)
        
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
                changes_for_db[field] = value.value if isinstance(value, models.GoalStatus) else value
            else:
                changes_for_db[field] = value

            val_kafka = value.value if isinstance(value, models.GoalStatus) else value
            changes_for_kafka[field] = val_kafka
        
        if not changes_for_db:
             today = datetime.now(timezone.utc).date()
             days_left = max((goal.finish_date - today).days, 0)
             return goal, days_left

        goal = await self.repo.update_fields(user_id, goal_id, changes_for_db)

        await self._check_and_process_achievement(goal)

        if changes_for_kafka:
            event_changed = {
                "event": "goal.changed", 
                "goal_id": str(goal_id), 
                "changes": changes_for_kafka
            }
            await self.repo.add_outbox_event(
                topic=settings.settings.kafka.kafka_topic_budget_events,
                event_data=event_changed
            )

        await self.repo.db.commit()

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
            logger.info(f"Transaction {event.transaction_id} duplicate. Checking state.")
            goal = await self.repo.get_goal_by_transaction_id(event.transaction_id)
            if not goal:
                return
            return

        event_updated = {
            "event": "goal.updated", 
            "goal_id": str(goal.id), 
            "current_value": goal.current_value,
            "status": goal.status
        }
        await self.repo.add_outbox_event(
            topic=settings.settings.kafka.kafka_topic_budget_events,
            event_data=event_updated
        )

        await self._check_and_process_achievement(goal)
        await self.repo.db.commit()

    async def _check_and_process_achievement(self, goal: models.Goal) -> bool:
        """Внутренний метод, не делает коммит сам, только добавляет в сессию."""
        achieved_goal = await self.repo.mark_achieved_if_eligible(goal.user_id, goal.id)
        
        if achieved_goal:
            goal.status = achieved_goal.status
            event_notif = {
                "event": "goal.alert", 
                "goal_id": str(goal.id), 
                "type": "achieved"
            }
            await self.repo.add_outbox_event(
                topic=settings.settings.kafka.kafka_topic_budget_notification,
                event_data=event_notif
            )
            return True

        elif (
            goal.current_value < goal.target_value
            and goal.status == models.GoalStatus.ACHIEVED.value
        ):
            new_status = models.GoalStatus.ONGOING.value
            await self.repo.update_fields(
                user_id=goal.user_id, 
                goal_id=goal.id, 
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
            expired_batch = await self.repo.get_expired_goals_batch(today, limit=BATCH_SIZE)
            if not expired_batch:
                break
            
            for goal in expired_batch:
                try:
                    event_updated = {"event": "goal.updated", "goal_id": str(goal.id), "status": "expired"}
                    await self.repo.add_outbox_event(settings.settings.kafka.kafka_topic_budget_events, event_updated)
                    
                    event_notif = {"event": "goal.expired", "goal_id": str(goal.id), "type": "expired"}
                    await self.repo.add_outbox_event(settings.settings.kafka.kafka_topic_budget_notification, event_notif)

                    await self.repo.update_status(goal.id, models.GoalStatus.EXPIRED.value)
                except Exception as e:
                    logger.error(f"Error processing expired {goal.id}: {e}")
            
            await self.repo.db.commit()

        while True:
            approaching_batch = await self.repo.get_approaching_goals_batch(today, limit=BATCH_SIZE)
            if not approaching_batch:
                break
            
            processed_ids = []
            for goal in approaching_batch:
                days_left = (goal.finish_date - today).days
                event_notif = {
                    "event": "goal.approaching", 
                    "goal_id": str(goal.id), 
                    "type": "approaching",
                    "days_left": days_left
                }
                await self.repo.add_outbox_event(settings.settings.kafka.kafka_topic_budget_notification, event_notif)
                processed_ids.append(goal.id)

            if processed_ids:
                await self.repo.update_last_checked(processed_ids)