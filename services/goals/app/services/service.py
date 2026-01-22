import logging
from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from app.core import config, exceptions, metrics
from app.domain.enums import (
    GoalEventType,
    GoalStatus,
    TransactionType,
    GoalPriority,
)
from app.infrastructure.db import models, uow
from app.domain.schemas import kafka as k_schemas, api as api_schemas

logger = logging.getLogger(__name__)
settings = config.settings

def _get_utc_today() -> date:
    """Возвращает текущую дату в UTC."""
    return datetime.now(timezone.utc).date()

def _create_outbox_event(
    event_type: GoalEventType,
    **kwargs,
) -> dict:
    """Создает событие для outbox_events."""
    return {
        "event_type": event_type.value,
        **kwargs,
    }

class GoalService:
    """Сервис для управления целями."""

    def __init__(self, uow: uow.UnitOfWork):
        self.uow = uow

    async def create_goal(
        self,
        user_id: UUID,
        request: api_schemas.CreateGoalRequest,
    ) -> api_schemas.CreateGoalResponse:
        """Создает новую цель."""
        if request.finish_date and request.finish_date <= _get_utc_today():
            raise exceptions.InvalidGoalDataError(
                "Finish date must be in the future"
            )

        goal = models.Goal(
            goal_id=uuid4(),
            user_id=user_id,
            name=request.name.strip(),
            target_value=request.target_value,
            current_value=Decimal("0"),
            finish_date=request.finish_date,
            status=GoalStatus.ONGOING.value,
            tags=request.tags,
            priority=request.priority.value if request.priority else None,
            is_archived=False,
        )

        async with self.uow:
            self.uow.goals.create(goal)

            event_data = _create_outbox_event(
                GoalEventType.CREATED,
                goal_id=str(goal.goal_id),
                user_id=str(user_id),
                name=goal.name,
                target_value=goal.target_value,
                finish_date=goal.finish_date,
                priority=goal.priority,
            )

            await self.uow.goals.add_outbox_event(
                topic=settings.KAFKA.KAFKA_TOPIC_BUDGET_EVENTS,
                event_data=event_data,
            )

        metrics.GOALS_CREATED_TOTAL.inc()
        return api_schemas.CreateGoalResponse(goal_id=goal.goal_id)

    async def get_goal_details(
        self,
        user_id: UUID,
        goal_id: UUID,
    ) -> api_schemas.GoalResponse:
        """Получает детали цели по ID."""
        async with self.uow:
            goal = await self.uow.goals.get_by_id(user_id, goal_id)

            if not goal:
                raise exceptions.GoalNotFoundError("Goal not found")

            net_change = await self.uow.goals.get_net_change_for_current_month(goal_id)
            rec_payment = goal.calculate_recommended_payment(net_change_this_month=net_change)
            days_left = goal.days_left

            response = api_schemas.GoalResponse.model_validate(goal)

        return response.model_copy(
            update={
                "days_left": days_left,
                "recommended_payment": rec_payment,
            }
        )

    async def get_main_goals(
        self,
        user_id: UUID,
    ) -> api_schemas.MainGoalsResponse:
        """Получает цели для главного экрана."""
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
        user_id: UUID,
        limit: int = 100,
        offset: int = 0,
        tags: list[str] | None = None,
        priorities: list[GoalPriority] = None,
        is_archived: bool = False,
    ) -> list[api_schemas.AllGoalsResponse]:
        """Получает список целей с фильтрами."""
        async with self.uow:
            goals = await self.uow.goals.get_all_goals(
                user_id,
                limit=limit,
                offset=offset,
                tags=tags,
                priorities=priorities,
                is_archived=is_archived,
            )

        return [
            api_schemas.AllGoalsResponse.model_validate(goal)
            for goal in goals
        ]

    async def update_goal(
        self,
        user_id: UUID,
        goal_id: UUID,
        request: api_schemas.GoalPatchRequest,
    ) -> api_schemas.GoalResponse:
        """Обновляет поля цели."""
        async with self.uow:
            goal = await self.uow.goals.get_for_update(goal_id)

            if not goal or goal.user_id != user_id:
                raise exceptions.GoalNotFoundError("Goal not found")

            update_data = request.model_dump(exclude_unset=True)

            if (
                "finish_date" in update_data
                and update_data["finish_date"]
                and update_data["finish_date"] <= _get_utc_today()
            ):
                raise exceptions.InvalidGoalDataError(
                    "Finish date must be in the future"
                )

            changes_for_db: dict = {}
            changes_for_kafka: dict = {}

            for field, value in update_data.items():
                if value is None and field != "finish_date":
                    continue

                db_value = value

                if isinstance(value, GoalPriority):
                    db_value = value.value

                if isinstance(db_value, str):
                    db_value = db_value.strip()

                changes_for_db[field] = db_value
                changes_for_kafka[field] = db_value

            if changes_for_db:
                goal = await self.uow.goals.update_fields(
                    user_id,
                    goal_id,
                    changes_for_db,
                )

                if "is_archived" not in changes_for_db:
                    await self._check_and_process_achievement_in_uow(goal)

            if changes_for_kafka:
                event = _create_outbox_event(
                    GoalEventType.CHANGED,
                    goal_id=str(goal_id),
                    changes=changes_for_kafka,
                )

                await self.uow.goals.add_outbox_event(
                    topic=settings.KAFKA.KAFKA_TOPIC_BUDGET_EVENTS,
                    event_data=event,
                )

            net_change = await self.uow.goals.get_net_change_for_current_month(goal_id)
            rec_payment = goal.calculate_recommended_payment(net_change_this_month=net_change)
            days_left = goal.days_left

            response = api_schemas.GoalResponse.model_validate(goal)

        return response.model_copy(
            update={
                "days_left": days_left,
                "recommended_payment": rec_payment,
            }
        )

    async def close_goal(
        self,
        user_id: UUID,
        goal_id: UUID,
    ) -> api_schemas.GoalStatusResponse:
        """Принудительно закрывает цель."""
        return await self._change_status_logic(
            user_id,
            goal_id,
            GoalStatus.CLOSED,
        )

    async def restore_goal(
        self,
        user_id: UUID,
        goal_id: UUID,
    ) -> api_schemas.GoalResponse:
        """Восстанавливает цель из закрытого состояния."""
        async with self.uow:
            goal = await self.uow.goals.get_by_id(user_id, goal_id)

            if not goal:
                raise exceptions.GoalNotFoundError("Goal not found")

            new_status = GoalStatus.ONGOING
            today = _get_utc_today()

            if goal.finish_date and goal.finish_date < today:
                new_status = GoalStatus.EXPIRED

            if goal.current_value >= goal.target_value:
                new_status = GoalStatus.ACHIEVED

        return await self._change_status_logic(
            user_id,
            goal_id,
            new_status,
        )

    async def _change_status_logic(
        self,
        user_id: UUID,
        goal_id: UUID,
        new_status: GoalStatus,
    ) -> api_schemas.GoalStatusResponse:
        """Изменяет статус цели."""
        async with self.uow:
            await self.uow.goals.update_fields(
                user_id,
                goal_id,
                {"status": new_status.value},
            )
            event = _create_outbox_event(
                GoalEventType.CHANGED,
                goal_id=str(goal_id),
                changes={"status": new_status.value},
            )
            await self.uow.goals.add_outbox_event(
                topic=settings.KAFKA.KAFKA_TOPIC_BUDGET_EVENTS,
                event_data=event,
            )

        return api_schemas.GoalStatusResponse(status=new_status)

    async def update_goal_balance(
        self,
        event: k_schemas.TransactionEvent,
    ) -> None:
        """Обновляет баланс цели на основе транзакции."""
        value_change = event.value * (
            Decimal(1) if event.type == TransactionType.INCOME else Decimal(-1)
        )

        async with self.uow:
            goal = await self.uow.goals.adjust_balance(
                user_id=event.user_id,
                goal_id=event.goal_id,
                amount_delta=value_change,
                transaction_id=event.transaction_id,
                raw_amount=event.value,
                transaction_type=event.type.value
            )

            if goal is None:
                logger.info(
                    "Transaction %s skipped (duplicate or closed goal).",
                    event.transaction_id,
                )
                return

            update_event = _create_outbox_event(
                GoalEventType.UPDATED,
                goal_id=str(goal.goal_id),
                current_value=goal.current_value,
                status=goal.status,
            )

            await self.uow.goals.add_outbox_event(
                topic=settings.KAFKA.KAFKA_TOPIC_BUDGET_EVENTS,
                event_data=update_event,
            )

            achieved_goal = (
                await self.uow.goals.mark_achieved_atomically(
                    event.user_id,
                    event.goal_id,
                )
            )

            if achieved_goal:
                event_achieved = _create_outbox_event(
                    GoalEventType.ALERT,
                    goal_id=str(achieved_goal.goal_id),
                    days_left=0,
                )

                await self.uow.goals.add_outbox_event(
                    topic=settings.KAFKA.KAFKA_TOPIC_BUDGET_NOTIFICATION,
                    event_data=event_achieved,
                )

                metrics.GOAL_ACHIEVEMENT_TIME.observe(
                    (
                        datetime.now(timezone.utc)
                        - achieved_goal.created_at
                    ).total_seconds()
                )
            else:
                reverted_goal = (
                    await self.uow.goals.revert_achievement_atomically(
                        event.user_id,
                        event.goal_id,
                    )
                )
                if reverted_goal:
                    logger.info(
                        "Goal %s reverted to ONGOING",
                        reverted_goal.goal_id,
                    )

    async def _check_and_process_achievement_in_uow(
        self,
        goal: models.Goal,
    ) -> bool:
        """Проверяет и обрабатывает достижение цели внутри UnitOfWork."""
        if goal.check_achievement():
            event = _create_outbox_event(
                GoalEventType.ALERT,
                goal_id=str(goal.goal_id),
                days_left=0,
            )

            await self.uow.goals.add_outbox_event(
                topic=settings.KAFKA.KAFKA_TOPIC_BUDGET_NOTIFICATION,
                event_data=event,
            )

            metrics.GOAL_ACHIEVEMENT_TIME.observe(
                (
                    datetime.now(timezone.utc) - goal.created_at
                ).total_seconds()
            )
            return True

        if goal.revert_achievement_if_needed():
            logger.info(
                "Goal %s reverted to ONGOING",
                goal.goal_id,
            )
            return True

        return False

    async def check_deadlines(self) -> None:
        """Проверяет цели на истечение сроков и отправляет уведомления."""
        logger.info("Starting daily deadline check task...")
        today = _get_utc_today()
        batch_size = 500
        last_id: UUID | None = None

        while True:
            async with self.uow:
                batch = await self.uow.goals.get_expired_goals_batch(
                    today=today,
                    limit=batch_size,
                    last_id=last_id,
                )

                if not batch:
                    break

                last_id = batch[-1].goal_id
                outbox_events: list[dict] = []
                expired_goal_ids: list[UUID] = []

                for goal in batch:
                    if not goal.finish_date:
                        continue

                    outbox_events.append(
                        {
                            "topic": settings.KAFKA.KAFKA_TOPIC_BUDGET_EVENTS,
                            "payload": _create_outbox_event(
                                GoalEventType.UPDATED,
                                goal_id=str(goal.goal_id),
                                status=GoalStatus.EXPIRED.value,
                            ),
                        }
                    )
                    outbox_events.append(
                        {
                            "topic": settings.KAFKA.KAFKA_TOPIC_BUDGET_NOTIFICATION,
                            "payload": _create_outbox_event(
                                GoalEventType.EXPIRED,
                                goal_id=str(goal.goal_id),
                                days_left=0,
                            ),
                        }
                    )

                    expired_goal_ids.append(goal.goal_id)

                if outbox_events:
                    await self.uow.goals.add_outbox_events(outbox_events)

                if expired_goal_ids:
                    await self.uow.goals.bulk_update_status(
                        expired_goal_ids,
                        GoalStatus.EXPIRED.value,
                    )

        while True:
            async with self.uow:
                approaching_batch = (
                    await self.uow.goals.get_approaching_goals_batch(
                        today,
                        limit=batch_size,
                    )
                )

                if not approaching_batch:
                    break

                outbox_events: list[dict] = []
                checked_ids: list[UUID] = []

                for goal in approaching_batch:
                    outbox_events.append(
                        {
                            "topic": settings.KAFKA.KAFKA_TOPIC_BUDGET_NOTIFICATION,
                            "payload": _create_outbox_event(
                                GoalEventType.APPROACHING,
                                goal_id=str(goal.goal_id),
                                type="approaching",
                                days_left=goal.days_left,
                            ),
                        }
                    )
                    checked_ids.append(goal.goal_id)

                if outbox_events:
                    await self.uow.goals.add_outbox_events(outbox_events)

                if checked_ids:
                    await self.uow.goals.update_last_checked(checked_ids)