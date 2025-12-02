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
    ) -> models.Goal:
        """Логика обновления цели."""
        goal = await self.repo.get_by_id(user_id, goal_id)
        if not goal:
            raise exceptions.GoalNotFoundError("Goal not found")

        changes = {}
        update_data = req.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if value is None:
                continue
            
            if field == 'status':
                try:
                    status_enum = models.GoalStatus(value)
                    setattr(goal, field, status_enum.value)
                except ValueError:
                    raise exceptions.InvalidGoalDataError(f"Invalid status: {value}")
            else:
                setattr(goal, field, value)
            
            changes[field] = value if not isinstance(value, date) else value.isoformat()

        achieved = False
        if (
            goal.current_value >= goal.target_value and 
            goal.status == models.GoalStatus.IN_PROGRESS.value
        ):
            goal.status = models.GoalStatus.ACHIEVED.value
            changes["status"] = models.GoalStatus.ACHIEVED.value
            achieved = True

        goal = await self.repo.update(goal)

        if changes:
            event_changed = {"event": "goal.changed", "goal_id": str(goal_id), "changes": changes}
            await self.kafka.send_budget_event(event_changed)
        
        if achieved:
            event_notif = {"event": "goal.alert", "goal_id": str(goal_id), "type": "achieved"}
            await self.kafka.send_notification(event_notif)
            
        return goal

    async def update_goal_balance(self, msg_data: dict):
        """Логика консьюмера."""
        try:
            goal_id = UUID(msg_data['account_id'])
            user_id = UUID(msg_data['user_id'])
            amount = Decimal(msg_data['amount'])
            direction = msg_data['direction']
        except (KeyError, ValueError, TypeError):
            raise exceptions.InvalidGoalDataError(f"Invalid message data: {msg_data}")

        goal = await self.repo.get_by_id(user_id, goal_id)
        if not goal:
            raise exceptions.GoalNotFoundError(f"Goal {goal_id} not found for user {user_id}")

        if direction == 'income':
            goal.current_value += amount
        elif direction == 'expense':
            goal.current_value = max(Decimal(0), goal.current_value - amount)

        achieved = False
        if (
            goal.current_value >= goal.target_value and 
            goal.status == models.GoalStatus.IN_PROGRESS.value
        ):
            goal.status = models.GoalStatus.ACHIEVED.value
            achieved = True

        await self.repo.update(goal)

        event_updated = {
            "event": "goal.updated", 
            "goal_id": str(goal_id), 
            "current_value": goal.current_value,
            "status": goal.status
        }
        await self.kafka.send_budget_event(event_updated)
        
        if achieved:
            event_notif = {"event": "goal.alert", "goal_id": str(goal_id), "type": "achieved"}
            await self.kafka.send_notification(event_notif)

    async def check_deadlines(self):
        """
        Логика Arq воркера.
        Выбирает только нужные цели и отправляет Kafka-ивенты параллельно.
        """
        logger.info("Starting daily check_goals_deadlines task...")
        today = datetime.now(timezone.utc).date()
        
        kafka_tasks = []
        goals_to_update = []
        
        expired_goals = await self.repo.get_expired_goals(today)
        
        for goal in expired_goals:
            goal.status = models.GoalStatus.EXPIRED.value
            goals_to_update.append(goal)
            
            event_updated = {"event": "goal.updated", "goal_id": str(goal.id), "status": "expired"}
            kafka_tasks.append(
                self.kafka.send_budget_event(event_updated)
            )
            
            event_notif = {"event": "goal.expired", "goal_id": str(goal.id), "type": "expired"}
            kafka_tasks.append(
                self.kafka.send_notification(event_notif)
            )
            
        approaching_goals = await self.repo.get_approaching_goals(today, days_notice=7)
        
        for goal in approaching_goals:
            days_left = (goal.finish_date - today).days
            goal.last_checked_date = datetime.now(timezone.utc)
            goals_to_update.append(goal)
            
            event_notif = {
                "event": "goal.approaching", 
                "goal_id": str(goal.id), 
                "type": "approaching",
                "days_left": days_left
            }
            kafka_tasks.append(
                self.kafka.send_notification(event_notif)
            )

        if goals_to_update:
            logger.info(f"Updating {len(goals_to_update)} goals ({len(expired_goals)} expired, {len(approaching_goals)} approaching)...")
            await self.repo.update_bulk(goals_to_update)
        
        if kafka_tasks:
            logger.info(f"Sending {len(kafka_tasks)} Kafka events in parallel...")
            await asyncio.gather(*kafka_tasks)
            
        logger.info(
            f"Finished check_goals_deadlines. Processed {len(expired_goals)} expired and {len(approaching_goals)} approaching goals."
        )