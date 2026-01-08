import logging
from uuid import UUID, uuid4
from decimal import Decimal
from datetime import datetime, timezone, date

from app.infrastructure.db import models, uow
from app.core import exceptions, config
from app.domain.schemas import api as api_schemas
from app.domain.schemas import kafka as k_schemas

logger = logging.getLogger(__name__)
settings = config.settings

def _get_utc_today() -> date:
    return datetime.now(timezone.utc).date()


def _get_days_left(finish_date: date) -> int:
    return max((finish_date - _get_utc_today()).days, 0)

def _create_outbox_event(event_type: k_schemas.GoalEventType, **kwargs) -> dict:
    """Фабрика для создания событий Outbox."""
    return {"event_type": event_type.value, **kwargs}

class GoalService:
    """Сервис для управления целями используя Unit of Work."""
    
    def __init__(self, uow: uow.UnitOfWork):
        self.uow = uow

    async def create_goal(self, user_id: UUID, request: api_schemas.CreateGoalRequest) -> api_schemas.CreateGoalResponse:
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
            status=api_schemas.GoalStatus.ONGOING.value,
        )
        
        async with self.uow:
            self.uow.goals.create(goal)
            
            event_data = _create_outbox_event(
                k_schemas.GoalEventType.CREATED,
                goal_id=str(goal.goal_id),
                user_id=str(user_id),
                name=goal.name,
                target_value=goal.target_value,
                finish_date=goal.finish_date
            )

            self.uow.goals.add_outbox_event(
                topic=settings.KAFKA.KAFKA_TOPIC_BUDGET_EVENTS,
                event_data=event_data,
            )

            return api_schemas.CreateGoalResponse(
                goal_id=goal.goal_id
            )

    async def get_goal_details(self, user_id: UUID, goal_id: UUID) -> api_schemas.GoalResponse:
        """Получение детальной информации о цели."""
        async with self.uow:
            goal = await self.uow.goals.get_by_id(user_id, goal_id)
            if not goal:
                raise exceptions.GoalNotFoundError("Goal not found")

            return api_schemas.GoalResponse.model_validate(
                goal,
                update={"days_left": _get_days_left(goal.finish_date)}
            )

    async def get_main_goals(self, user_id: UUID) -> api_schemas.MainGoalsResponse:
        """Получение целей для главного экрана."""
        async with self.uow:
            goals = await self.uow.goals.get_main_goals(user_id)
            return api_schemas.MainGoalsResponse(
                goals=[
                    api_schemas.MainGoalInfo.model_validate(goal)
                    for goal in goals
                ]
            )

    async def get_all_goals(
        self,
        user_id: UUID
    ) -> list[api_schemas.AllGoalsResponse]:
        async with self.uow:
            goals = await self.uow.goals.get_all_goals(user_id)

            return [
                api_schemas.AllGoalsResponse.model_validate(goal)
                for goal in goals
            ]

    async def update_goal(
        self, user_id: UUID, goal_id: UUID, request: api_schemas.GoalPatchRequest
    ) -> api_schemas.GoalResponse:
        """Обновление цели."""
        async with self.uow:
            goal = await self.uow.goals.get_by_id(user_id, goal_id)
            if not goal:
                raise exceptions.GoalNotFoundError("Goal not found")

            update_data = request.model_dump(exclude_unset=True)
            if not update_data:
                return api_schemas.GoalResponse.model_validate(
                    goal,
                    update={"days_left": _get_days_left(goal.finish_date)}
                )

            if "finish_date" in update_data and update_data["finish_date"]:
                if update_data["finish_date"] <= _get_utc_today():
                    raise exceptions.InvalidGoalDataError("Finish date must be in the future")

            changes_for_db = {}
            changes_for_kafka = {}

            for field, value in update_data.items():
                if value is None: continue
                db_value = value.value if isinstance(value, api_schemas.GoalStatus) else value
                if isinstance(db_value, str): db_value = db_value.strip()
                changes_for_db[field] = db_value
                changes_for_kafka[field] = db_value
            
            if not changes_for_db:
                return api_schemas.GoalResponse.model_validate(
                    goal,
                    update={"days_left": _get_days_left(goal.finish_date)}
                )

            goal = await self.uow.goals.update_fields(user_id, goal_id, changes_for_db)
            await self._check_and_process_achievement_in_uow(goal)

            if changes_for_kafka:
                event = _create_outbox_event(
                    k_schemas.GoalEventType.CHANGED,
                    goal_id=str(goal_id),
                    changes=changes_for_kafka
                )
                self.uow.goals.add_outbox_event(
                    topic=settings.KAFKA.KAFKA_TOPIC_BUDGET_EVENTS,
                    event_data=event
                )
            return api_schemas.GoalResponse.model_validate(
                goal,
                update={"days_left": _get_days_left(goal.finish_date)}
            )

    async def update_goal_balance(self, event: k_schemas.TransactionEvent) -> None:
        """Обработка события изменения баланса из Kafka (идемпотентная)."""
        value_change = event.value * (
            Decimal(1) if event.type == k_schemas.TransactionType.INCOME else Decimal(-1)
        )
        
        async with self.uow:
            goal = await self.uow.goals.adjust_balance(
                event.user_id, event.goal_id, value_change, event.transaction_id
            )
            if goal is None:
                logger.info(f"Transaction {event.transaction_id} duplicate. Skipping.")
                return

            update_event = _create_outbox_event(
                k_schemas.GoalEventType.UPDATED,
                goal_id=str(goal.goal_id),
                current_value=goal.current_value,
                status=goal.status
            )
            self.uow.goals.add_outbox_event(
                topic=settings.KAFKA.KAFKA_TOPIC_BUDGET_EVENTS,
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
                k_schemas.GoalEventType.ALERT,
                goal_id=str(goal.goal_id),
                days_left=0
            )
            self.uow.goals.add_outbox_event(
                topic=settings.KAFKA.KAFKA_TOPIC_BUDGET_NOTIFICATION,
                event_data=event
            )
            logger.info(f"Goal {goal.goal_id} achieved")
            return True

        elif (
            goal.current_value < goal.target_value
            and goal.status == api_schemas.GoalStatus.ACHIEVED.value
        ):
            new_status = api_schemas.GoalStatus.ONGOING.value
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
        batch_size = 500
        last_id: UUID | None = None

        while True:
            async with self.uow:
                batch = await self.uow.goals.get_expired_goals_batch(
                    today=today, limit=batch_size, last_id=last_id
                )
                if not batch:
                    break
                
                last_id = batch[-1].goal_id
                
                outbox_events = []
                expired_goal_ids = []

                for goal in batch:
                    outbox_events.append({
                        "topic": settings.KAFKA.KAFKA_TOPIC_BUDGET_EVENTS,
                        "payload": _create_outbox_event(
                            k_schemas.GoalEventType.UPDATED,
                            goal_id=str(goal.goal_id),
                            status=api_schemas.GoalStatus.EXPIRED.value
                        )
                    })
                    
                    outbox_events.append({
                        "topic": settings.KAFKA.KAFKA_TOPIC_BUDGET_NOTIFICATION,
                        "payload": _create_outbox_event(
                            k_schemas.GoalEventType.EXPIRED,
                            goal_id=str(goal.goal_id),
                            days_left=0
                        )
                    })
                    
                    expired_goal_ids.append(goal.goal_id)

                if outbox_events:
                    await self.uow.goals.bulk_add_outbox_events(outbox_events)
                
                if expired_goal_ids:
                    await self.uow.goals.bulk_update_status(
                        expired_goal_ids, 
                        api_schemas.GoalStatus.EXPIRED.value
                    )
                
                logger.info(f"Processed batch of {len(batch)} expired goals.")

        while True:
            async with self.uow:
                approaching_batch = await self.uow.goals.get_approaching_goals_batch(
                    today, limit=batch_size
                )
                if not approaching_batch:
                    break
                
                outbox_events = []
                checked_ids = []

                for goal in approaching_batch:
                    days_left = _get_days_left(goal.finish_date)
                    
                    outbox_events.append({
                        "topic": settings.KAFKA.KAFKA_TOPIC_BUDGET_NOTIFICATION,
                        "payload": _create_outbox_event(
                            k_schemas.GoalEventType.APPROACHING, 
                            goal_id=str(goal.goal_id), 
                            type="approaching", 
                            days_left=days_left
                        )
                    })
                    checked_ids.append(goal.goal_id)

                if outbox_events:
                    await self.uow.goals.bulk_add_outbox_events(outbox_events)
                
                if checked_ids:
                    await self.uow.goals.update_last_checked(checked_ids)
                
                logger.info(f"Processed batch of {len(approaching_batch)} approaching goals.")