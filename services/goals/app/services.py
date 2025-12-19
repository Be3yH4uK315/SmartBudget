import logging
from uuid import UUID, uuid4
from decimal import Decimal
from datetime import datetime, timezone, date

from app import (
    models, 
    repositories, 
    exceptions, 
    schemas,
    settings
)

logger = logging.getLogger(__name__)

def _get_days_left(finish_date: date) -> int:
    """Расчет дней до срока."""
    today = datetime.now(timezone.utc).date()
    return max((finish_date - today).days, 0)

def _create_outbox_event(event_type: str, **kwargs) -> dict:
    """Фабрика для создания событий Outbox."""
    return {"event": event_type, **kwargs}

class GoalService:
    """Сервис для управления целями пользователя."""
    
    def __init__(self, repository: repositories.GoalRepository):
        self.repository = repository

    async def create_goal(
        self, 
        user_id: UUID, 
        request: schemas.CreateGoalRequest
    ) -> models.Goal:
        """Создание новой цели."""
        if request.finish_date <= datetime.now(timezone.utc).date():
            raise exceptions.InvalidGoalDataError("Finish date must be in the future")
        
        goal_id = uuid4()
        new_goal = models.Goal(
            goal_id=goal_id,
            user_id=user_id,
            name=request.name.strip(),
            target_value=request.target_value,
            current_value=Decimal(0),
            finish_date=request.finish_date,
            status=models.GoalStatus.ONGOING.value
        )
        
        goal = await self.repository.create(new_goal)
        
        event = _create_outbox_event(
            "goal.created",
            goal_id=str(goal.goal_id),
            user_id=str(user_id),
            name=goal.name,
            target_value=float(goal.target_value),
            finish_date=goal.finish_date.isoformat()
        )

        await self.repository.add_outbox_event(
            topic=settings.settings.KAFKA.KAFKA_TOPIC_BUDGET_EVENTS,
            event_data=event
        )
        await self.repository.db.commit()
        await self.repository.db.refresh(goal)
        
        return goal

    async def get_goal_details(
        self, 
        user_id: UUID, 
        goal_id: UUID
    ) -> tuple[models.Goal, int]:
        """Получение детальной информации о цели."""
        goal = await self.repository.get_by_id(user_id, goal_id)
        if not goal:
            raise exceptions.GoalNotFoundError("Goal not found")

        days_left = _get_days_left(goal.finish_date)
        return goal, days_left

    async def get_main_goals(self, user_id: UUID) -> list[models.Goal]:
        """Получение целей для главного экрана."""
        return await self.repository.get_main_goals(user_id)

    async def get_all_goals(self, user_id: UUID) -> list[models.Goal]:
        """Получение всех целей пользователя."""
        return await self.repository.get_all_goals(user_id)

    async def update_goal(
        self, 
        user_id: UUID, 
        goal_id: UUID, 
        request: schemas.GoalPatchRequest
    ) -> tuple[models.Goal, int]:
        """Обновление цели."""
        goal = await self.repository.get_by_id(user_id, goal_id)
        if not goal:
            raise exceptions.GoalNotFoundError("Goal not found")

        update_data = request.model_dump(exclude_unset=True)
        if not update_data:
            days_left = _get_days_left(goal.finish_date)
            return goal, days_left

        if "finish_date" in update_data and update_data["finish_date"]:
            if update_data["finish_date"] <= datetime.now(timezone.utc).date():
                raise exceptions.InvalidGoalDataError("Finish date must be in the future")

        changes_for_db = {}
        changes_for_kafka = {}

        for field, value in update_data.items():
            if value is None:
                continue
            
            db_value = value.value if isinstance(value, models.GoalStatus) else value
            if isinstance(db_value, str):
                db_value = db_value.strip()
            
            changes_for_db[field] = db_value
            changes_for_kafka[field] = db_value
        
        if not changes_for_db:
            days_left = _get_days_left(goal.finish_date)
            return goal, days_left

        goal = await self.repository.update_fields(user_id, goal_id, changes_for_db)
        await self._check_and_process_achievement(goal)

        if changes_for_kafka:
            event = _create_outbox_event(
                "goal.changed",
                goal_id=str(goal_id),
                changes=changes_for_kafka
            )
            await self.repository.add_outbox_event(
                topic=settings.settings.KAFKA.KAFKA_TOPIC_BUDGET_EVENTS,
                event_data=event
            )

        await self.repository.db.commit()
        days_left = _get_days_left(goal.finish_date)
        return goal, days_left

    async def update_goal_balance(self, event: schemas.TransactionEvent) -> None:
        """Обработка события изменения баланса из Kafka (идемпотентная)."""
        value_change = event.value * (
            Decimal(1) if event.type is schemas.TransactionType.INCOME else Decimal(-1)
        )
        
        goal = await self.repository.adjust_balance(
            event.user_id, 
            event.goal_id, 
            value_change, 
            event.transaction_id
        )

        if goal is None:
            logger.info(f"Transaction {event.transaction_id} already processed")
            return

        update_event = _create_outbox_event(
            "goal.updated",
            goal_id=str(goal.goal_id),
            current_value=float(goal.current_value),
            status=goal.status
        )
        await self.repository.add_outbox_event(
            topic=settings.settings.KAFKA.KAFKA_TOPIC_BUDGET_EVENTS,
            event_data=update_event
        )

        await self._check_and_process_achievement(goal)
        await self.repository.db.commit()

    async def _check_and_process_achievement(self, goal: models.Goal) -> bool:
        """Проверка и обработка достижения цели."""
        achieved_goal = await self.repository.mark_achieved_if_eligible(
            goal.user_id, 
            goal.goal_id
        )
        
        if achieved_goal:
            goal.status = achieved_goal.status
            event = _create_outbox_event(
                "goal.alert",
                goal_id=str(goal.goal_id),
                type="expiring"
            )
            await self.repository.add_outbox_event(
                topic=settings.settings.KAFKA.KAFKA_TOPIC_BUDGET_NOTIFICATION,
                event_data=event
            )
            logger.info(f"Goal {goal.goal_id} achieved")
            return True

        elif (
            goal.current_value < goal.target_value
            and goal.status == models.GoalStatus.ACHIEVED.value
        ):
            new_status = models.GoalStatus.ONGOING.value
            await self.repository.update_fields(
                user_id=goal.user_id, 
                goal_id=goal.goal_id, 
                changes={"status": new_status}
            )
            goal.status = new_status
            logger.info(f"Goal {goal.goal_id} reverted to ONGOING")
            return True
            
        return False

    async def check_deadlines(self) -> None:
        """Крон-задача для проверки сроков целей (запускается ежедневно)."""
        logger.info("Starting daily deadline check task...")
        today = datetime.now(timezone.utc).date()
        batch_size = 100
        processed_expired = 0
        processed_approaching = 0
        failed_count = 0

        try:
            while True:
                expired_batch = await self.repository.get_expired_goals_batch(
                    today, 
                    limit=batch_size
                )
                if not expired_batch:
                    break
                
                for goal in expired_batch:
                    try:
                        await self.repository.add_outbox_event(
                            settings.settings.KAFKA.KAFKA_TOPIC_BUDGET_EVENTS,
                            _create_outbox_event(
                                "goal.updated",
                                goal_id=str(goal.goal_id),
                                status="expired"
                            )
                        )
                        
                        await self.repository.add_outbox_event(
                            settings.settings.KAFKA.KAFKA_TOPIC_BUDGET_NOTIFICATION,
                            _create_outbox_event(
                                "goal.expired",
                                goal_id=str(goal.goal_id),
                                type="expired"
                            )
                        )

                        await self.repository.update_status(
                            goal.goal_id, 
                            models.GoalStatus.EXPIRED.value
                        )
                        processed_expired += 1
                    except Exception as e:
                        logger.error(f"Error processing expired goal {goal.goal_id}: {e}")
                        failed_count += 1
                
                await self.repository.db.commit()

            while True:
                approaching_batch = await self.repository.get_approaching_goals_batch(
                    today, 
                    limit=batch_size
                )
                if not approaching_batch:
                    break
                
                processed_ids = []
                for goal in approaching_batch:
                    try:
                        days_left = _get_days_left(goal.finish_date)
                        event = _create_outbox_event(
                            "goal.approaching",
                            goal_id=str(goal.goal_id),
                            type="approaching",
                            days_left=days_left
                        )
                        await self.repository.add_outbox_event(
                            settings.settings.KAFKA.KAFKA_TOPIC_BUDGET_NOTIFICATION,
                            event_data=event
                        )
                        processed_ids.append(goal.goal_id)
                        processed_approaching += 1
                    except Exception as e:
                        logger.error(f"Error processing approaching goal {goal.goal_id}: {e}")
                        failed_count += 1

                if processed_ids:
                    await self.repository.update_last_checked(processed_ids)
                await self.repository.db.commit()

            logger.info(
                f"Deadline check completed: "
                f"expired={processed_expired}, "
                f"approaching={processed_approaching}, "
                f"failed={failed_count}"
            )
        except Exception as e:
            logger.critical(f"Fatal error in check_deadlines: {e}", exc_info=True)
            raise