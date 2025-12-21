import logging
from typing import Any
from uuid import UUID, uuid4
from decimal import Decimal
from datetime import datetime, timezone, date

from app import (
    models, 
    exceptions, 
    schemas,
    settings,
    unit_of_work
)

logger = logging.getLogger(__name__)

def _get_utc_today() -> date:
    return datetime.now(timezone.utc).date()


def _get_days_left(finish_date: date) -> int:
    return max((finish_date - _get_utc_today()).days, 0)

def create_goal_event(
    event_type: schemas.GoalEventType,
    goal_id: str,
    payload: dict[str, Any] | None = None,
) -> dict:
    return {
        "event": event_type.value,
        "goal_id": goal_id,
        "payload": payload or {},
    }

def _create_outbox_event(event_type: schemas.GoalEventType, **kwargs) -> dict:
    """Фабрика для создания событий Outbox."""
    return {"event_type": event_type, **kwargs}

class GoalService:
    """Сервис для управления целями используя Unit of Work."""
    
    def __init__(self, uow: unit_of_work.UnitOfWork):
        self.uow = uow

    async def create_goal(self, user_id: UUID, request: schemas.CreateGoalRequest) -> models.Goal:
        """Создание новой цели."""
        if request.finish_date <= _get_utc_today():
            raise exceptions.InvalidGoalDataError("Finish date must be in the future")
        
        goal = models.Goal(
            goal_id=uuid4(),
            user_id=user_id,
            name=request.name.strip(),
            target_value=request.target_value,
            current_value=Decimal("0"),
            finish_date=request.finish_date,
            status=schemas.GoalStatus.ONGOING.value,
        )
        
        async with self.uow:
            self.uow.goals.create(goal)
            
            event_data = _create_outbox_event(
                schemas.GoalEventType.CREATED.value,
                goal_id=str(goal.goal_id),
                user_id=str(user_id),
                name=goal.name,
                target_value=goal.target_value,
                finish_date=goal.finish_date
            )

            self.uow.goals.add_outbox_event(
                topic=settings.settings.KAFKA.KAFKA_TOPIC_BUDGET_EVENTS,
                event_data=event_data,
            )

            return goal
        
    async def get_goal_details(self, user_id: UUID, goal_id: UUID) -> tuple[models.Goal, int]:
        """Получение детальной информации о цели."""
        async with self.uow:
            goal = await self.uow.goals.get_by_id(user_id, goal_id)
            if not goal:
                raise exceptions.GoalNotFoundError("Goal not found")
            days_left = _get_days_left(goal.finish_date)
            return goal, days_left

    async def get_main_goals(self, user_id: UUID) -> list[models.Goal]:
        """Получение целей для главного экрана."""
        async with self.uow:
            return await self.uow.goals.get_main_goals(user_id)

    async def get_all_goals(self, user_id: UUID) -> list[models.Goal]:
        """Получение всех целей пользователя."""
        async with self.uow:
            return await self.uow.goals.get_all_goals(user_id)

    async def update_goal(
        self, user_id: UUID, goal_id: UUID, request: schemas.GoalPatchRequest
    ) -> tuple[models.Goal, int]:
        """Обновление цели."""
        async with self.uow:
            goal = await self.uow.goals.get_by_id(user_id, goal_id)
            if not goal:
                raise exceptions.GoalNotFoundError("Goal not found")

            update_data = request.model_dump(exclude_unset=True)
            if not update_data:
                return goal, _get_days_left(goal.finish_date)

            if "finish_date" in update_data and update_data["finish_date"]:
                if update_data["finish_date"] <= _get_utc_today():
                    raise exceptions.InvalidGoalDataError("Finish date must be in the future")

            changes_for_db = {}
            changes_for_kafka = {}

            for field, value in update_data.items():
                if value is None: continue
                db_value = value.value if isinstance(value, schemas.GoalStatus) else value
                if isinstance(db_value, str): db_value = db_value.strip()
                changes_for_db[field] = db_value
                changes_for_kafka[field] = db_value
            
            if not changes_for_db:
                return goal, _get_days_left(goal.finish_date)

            goal = await self.uow.goals.update_fields(user_id, goal_id, changes_for_db)
            await self._check_and_process_achievement_in_uow(goal)

            if changes_for_kafka:
                event = _create_outbox_event(
                    schemas.GoalEventType.CHANGED.value,
                    goal_id=str(goal_id),
                    changes=changes_for_kafka
                )
                self.uow.goals.add_outbox_event(
                    topic=settings.settings.KAFKA.KAFKA_TOPIC_BUDGET_EVENTS,
                    event_data=event
                )
            return goal, _get_days_left(goal.finish_date)

    async def update_goal_balance(self, event: schemas.TransactionEvent) -> None:
        """Обработка события изменения баланса из Kafka (идемпотентная)."""
        value_change = event.value * (
            Decimal(1) if event.type == schemas.TransactionType.INCOME else Decimal(-1)
        )
        
        async with self.uow:
            goal = await self.uow.goals.adjust_balance(
                event.user_id, event.goal_id, value_change, event.transaction_id
            )
            if goal is None:
                logger.info(f"Transaction {event.transaction_id} duplicate. Skipping.")
                return

            update_event = _create_outbox_event(
                schemas.GoalEventType.UPDATED.value,
                goal_id=str(goal.goal_id),
                current_value=goal.current_value,
                status=goal.status
            )
            self.uow.goals.add_outbox_event(
                topic=settings.settings.KAFKA.KAFKA_TOPIC_BUDGET_EVENTS,
                event_data=update_event
            )

            await self._check_and_process_achievement_in_uow(goal)

    async def _check_and_process_achievement_in_uow(self, goal: models.Goal) -> bool:
        """Внутренний метод, работает в контексте текущего UoW."""
        achieved_goal = await self.uow.goals.mark_achieved_if_eligible(
            goal.user_id, goal.goal_id
        )
        
        if achieved_goal:
            goal.status = achieved_goal.status
            event = _create_outbox_event(
                schemas.GoalEventType.ALERT.value,
                goal_id=str(goal.goal_id),
                days_left=0
            )
            self.uow.goals.add_outbox_event(
                topic=settings.settings.KAFKA.KAFKA_TOPIC_BUDGET_NOTIFICATION,
                event_data=event
            )
            logger.info(f"Goal {goal.goal_id} achieved")
            return True

        elif (
            goal.current_value < goal.target_value
            and goal.status == schemas.GoalStatus.ACHIEVED.value
        ):
            new_status = schemas.GoalStatus.ONGOING.value
            await self.uow.goals.update_fields(
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
        today = _get_utc_today()
        batch_size = 100
        last_id: UUID | None = None

        while True:
            async with self.uow:
                batch = await self.uow.goals.get_expired_goals_batch(
                    today=today, limit=batch_size, last_id=last_id
                )
                if not batch:
                    break
                
                last_id_in_batch = batch[-1].goal_id

                for goal in batch:
                    try:
                        self.uow.goals.add_outbox_event(
                            settings.settings.KAFKA.KAFKA_TOPIC_BUDGET_EVENTS,
                            _create_outbox_event(
                                schemas.GoalEventType.UPDATED.value,
                                goal_id=str(goal.goal_id),
                                status=schemas.GoalStatus.EXPIRED.value
                            )
                        )
                        self.uow.goals.add_outbox_event(
                            settings.settings.KAFKA.KAFKA_TOPIC_BUDGET_NOTIFICATION,
                            _create_outbox_event(
                                schemas.GoalEventType.EXPIRED.value,
                                goal_id=str(goal.goal_id),
                                days_left=0
                            )
                        )

                        await self.uow.goals.update_status(
                            goal.goal_id,
                            schemas.GoalStatus.EXPIRED.value
                        )
                    except Exception as e:
                        logger.error(f"Error processing expired goal {goal.goal_id}: {e}")
                        continue

                last_id = last_id_in_batch

        while True:
            async with self.uow:
                approaching_batch = await self.uow.goals.get_approaching_goals_batch(
                    today, limit=batch_size
                )
                if not approaching_batch:
                    break
                
                processed_ids = []
                for goal in approaching_batch:
                    try:
                        days_left = _get_days_left(goal.finish_date)
                        event = _create_outbox_event(
                            schemas.GoalEventType.APPROACHING.value, 
                            goal_id=str(goal.goal_id), 
                            type="approaching", 
                            days_left=days_left
                        )
                        self.uow.goals.add_outbox_event(
                            settings.settings.KAFKA.KAFKA_TOPIC_BUDGET_NOTIFICATION, 
                            event_data=event
                        )
                        processed_ids.append(goal.goal_id)
                    except Exception as e:
                        logger.error(f"Error processing approaching goal {goal.goal_id}: {e}")
                        continue

                if processed_ids:
                    await self.uow.goals.update_last_checked(processed_ids)