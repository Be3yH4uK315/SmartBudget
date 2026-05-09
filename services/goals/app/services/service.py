import logging
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

from app.core import config, exceptions, metrics
from app.domain.enums import GoalEventType, GoalPriority, GoalStatus, TransactionType
from app.domain.schemas import api as api_schemas
from app.domain.schemas import kafka as kafka_schemas
from app.infrastructure.db import models, uow

logger = logging.getLogger(__name__)
settings = config.settings

DEADLINE_BATCH_SIZE = 500
ALMOST_ACHIEVED_PERCENT = 80.0


def _get_utc_today() -> date:
    """Возвращает текущую дату в UTC."""
    return datetime.now(timezone.utc).date()


def _create_outbox_event(
    event_type: GoalEventType,
    **payload_fields,
) -> dict:
    """Создает payload события для outbox_events."""
    return {
        "event_type": event_type.value,
        **payload_fields,
    }


def _notification_event_id(
    event_name: str,
    goal_id: UUID | str,
    occurrence_key: str | None = None,
) -> UUID:
    """Создает детерминированный event_id для notification service."""
    key = f"smartbudget:notifications:{event_name}:{goal_id}"

    if occurrence_key:
        key = f"{key}:{occurrence_key}"

    return uuid5(NAMESPACE_URL, key)


def _create_notification_event(
    event_name: str,
    user_id: UUID,
    payload: dict,
    event_id: UUID | None = None,
) -> dict:
    """Создает событие для notification service."""
    return {
        "event_id": str(event_id or uuid4()),
        "event_type": event_name,
        "user_id": str(user_id),
        "payload": payload,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _decimal_to_float(value: Decimal | int | float | None) -> float:
    """Преобразует Decimal/int/float/None в float для notification payload."""
    if value is None:
        return 0.0

    return float(value)


def _goal_current_percent(goal: models.Goal) -> float:
    """Возвращает процент достижения цели."""
    if not goal.target_amount:
        return 0.0

    percent = (goal.current_amount / goal.target_amount) * Decimal("100")
    bounded_percent = min(percent, Decimal("100")).quantize(Decimal("0.01"))

    return float(bounded_percent)


def _goal_recommended_payment(goal: models.Goal) -> float:
    """Возвращает рекомендованный платеж по цели в float."""
    if goal.created_at is None:
        goal.created_at = datetime.now(timezone.utc)

    value = goal.calculate_recommended_payment()

    return _decimal_to_float(value)


def _previous_month_period(today: date) -> tuple[datetime, datetime, str]:
    """Возвращает начало прошлого месяца, начало текущего месяца и ключ YYYY-MM."""
    current_month_start = datetime(
        today.year,
        today.month,
        1,
        tzinfo=timezone.utc,
    )
    previous_month_last_day = current_month_start - timedelta(days=1)
    previous_month_start = datetime(
        previous_month_last_day.year,
        previous_month_last_day.month,
        1,
        tzinfo=timezone.utc,
    )
    month_key = previous_month_start.strftime("%Y-%m")

    return previous_month_start, current_month_start, month_key


def _transaction_amount_delta(
    amount: Decimal,
    transaction_type: TransactionType,
) -> Decimal:
    """Возвращает изменение баланса цели по типу транзакции."""
    if transaction_type == TransactionType.INCOME:
        return amount

    return -amount


class GoalService:
    """Сервис управления целями."""

    def __init__(self, uow: uow.UnitOfWork) -> None:
        self.uow = uow

    async def create_goal(
        self,
        user_id: UUID,
        request: api_schemas.CreateGoalRequest,
    ) -> api_schemas.CreateGoalResponse:
        """Создает новую цель."""
        self._validate_finish_date(request.finish_date)

        goal = models.Goal(
            goal_id=uuid4(),
            user_id=user_id,
            name=request.name.strip(),
            target_amount=request.target_amount,
            current_amount=Decimal("0"),
            finish_date=request.finish_date,
            status=GoalStatus.ONGOING.value,
            tags=request.tags,
            priority=request.priority.value if request.priority else None,
            is_archived=False,
        )

        async with self.uow:
            self.uow.goals.create(goal)
            self._add_goal_created_events(goal, user_id)

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

            response = await self._build_goal_response(goal)

        return response

    async def get_main_goals(
        self,
        user_id: UUID,
    ) -> api_schemas.MainGoalsResponse:
        """Получает цели для главного экрана."""
        async with self.uow:
            goals = await self.uow.goals.get_main_goals(user_id)

        return api_schemas.MainGoalsResponse(
            goals=[api_schemas.MainGoalInfo.model_validate(goal) for goal in goals],
        )

    async def search_goals(
        self,
        user_id: UUID,
        query: str,
        limit: int,
    ) -> list[api_schemas.GoalSearchResponse]:
        """Ищет цели пользователя по названию."""
        normalized_query = query.strip()
        if not normalized_query:
            return []

        async with self.uow:
            goals = await self.uow.goals.search_goals(
                user_id,
                normalized_query,
                limit,
            )

        return [api_schemas.GoalSearchResponse.model_validate(goal) for goal in goals]

    async def get_all_goals(
        self,
        user_id: UUID,
        limit: int = 100,
        offset: int = 0,
        tags: list[str] | None = None,
        priorities: list[GoalPriority] | None = None,
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

        return [api_schemas.AllGoalsResponse.model_validate(goal) for goal in goals]

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
            self._validate_finish_date(update_data.get("finish_date"))

            changes_for_db, changes_for_kafka = self._prepare_goal_changes(update_data)

            if changes_for_db:
                previous_status = goal.status
                goal = await self._apply_goal_changes(
                    user_id=user_id,
                    goal_id=goal_id,
                    goal=goal,
                    changes_for_db=changes_for_db,
                )

                if "is_archived" not in changes_for_db:
                    await self._check_and_process_achievement_in_uow(goal)

                if goal.status != previous_status:
                    changes_for_kafka["status"] = goal.status

            if changes_for_kafka:
                self._add_goal_changed_event(goal_id, changes_for_kafka)

            response = await self._build_goal_response(goal)

        return response

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
    ) -> api_schemas.GoalStatusResponse:
        """Восстанавливает цель из закрытого состояния."""
        async with self.uow:
            goal = await self.uow.goals.get_by_id(user_id, goal_id)

            if not goal:
                raise exceptions.GoalNotFoundError("Goal not found")

            new_status = self._resolve_restored_status(goal)

        return await self._change_status_logic(
            user_id,
            goal_id,
            new_status,
        )

    async def toggle_archive_status(
        self,
        user_id: UUID,
        goal_id: UUID,
    ) -> api_schemas.GoalArchiveResponse:
        """Переключает архивный статус цели."""
        async with self.uow:
            goal = await self.uow.goals.get_by_id(user_id, goal_id)

            if not goal:
                raise exceptions.GoalNotFoundError("Goal not found")

            if goal.status not in {GoalStatus.CLOSED.value, GoalStatus.ACHIEVED.value}:
                raise exceptions.InvalidGoalDataError(
                    "Only closed or achieved goals can be archived",
                )

            updated = await self.uow.goals.update_fields(
                user_id,
                goal_id,
                {"is_archived": not goal.is_archived},
            )

        return api_schemas.GoalArchiveResponse(is_archived=updated.is_archived)

    async def update_goal_balance(
        self,
        event: kafka_schemas.TransactionEvent,
    ) -> None:
        """Обновляет баланс цели на основе транзакции."""
        value_change = _transaction_amount_delta(
            event.amount,
            event.transaction_type,
        )

        async with self.uow:
            goal = await self.uow.goals.adjust_balance(
                user_id=event.user_id,
                goal_id=event.goal_id,
                amount_delta=value_change,
                transaction_id=event.transaction_id,
                raw_amount=event.amount,
                transaction_type=event.transaction_type.value,
                occurred_at=event.occurred_at,
            )

            if goal is None:
                logger.info(
                    "Transaction %s skipped: duplicate transaction or closed goal",
                    event.transaction_id,
                )
                return

            self._add_goal_updated_event(goal)

            achieved_goal = await self.uow.goals.mark_achieved_atomically(
                event.user_id,
                event.goal_id,
            )

            if achieved_goal:
                await self._process_achieved_goal_in_uow(achieved_goal)
                return

            reverted_goal = await self.uow.goals.revert_achievement_atomically(
                event.user_id,
                event.goal_id,
            )

            if reverted_goal:
                logger.info("Goal %s reverted to ONGOING", reverted_goal.goal_id)
                return

            await self._add_almost_achieved_notification_in_uow(goal)

    async def rollback_goal_transaction(
        self,
        event: kafka_schemas.TransactionDeletedEvent,
    ) -> None:
        """Откатывает баланс цели при удалении транзакции."""
        async with self.uow:
            goal = await self.uow.goals.rollback_transaction(
                user_id=event.user_id,
                transaction_id=event.transaction_id,
            )

            if goal is None:
                logger.info(
                    "Goal transaction %s skipped for rollback",
                    event.transaction_id,
                )
                return

            self._add_goal_updated_event(goal)

            achieved_goal = await self.uow.goals.mark_achieved_atomically(
                event.user_id,
                goal.goal_id,
            )

            if achieved_goal:
                await self._process_achieved_goal_in_uow(achieved_goal)
                return

            reverted_goal = await self.uow.goals.revert_achievement_atomically(
                event.user_id,
                goal.goal_id,
            )

            if reverted_goal:
                logger.info(
                    "Goal %s reverted to ONGOING after transaction rollback",
                    reverted_goal.goal_id,
                )
                return

            await self._add_almost_achieved_notification_in_uow(goal)

    async def check_deadlines(self) -> None:
        """Проверяет цели на истечение сроков и отправляет уведомления."""
        logger.info("Starting daily deadline check task")

        today = _get_utc_today()

        await self._process_expired_goals(today)
        await self._process_approaching_goals(today)
        await self._check_missed_monthly_payments(today, DEADLINE_BATCH_SIZE)

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
            self._add_goal_changed_event(
                goal_id,
                {"status": new_status.value},
            )

        return api_schemas.GoalStatusResponse(status=new_status)

    async def _build_goal_response(self, goal: models.Goal) -> api_schemas.GoalResponse:
        """Формирует response-модель с расчетными полями цели."""
        net_change = await self.uow.goals.get_net_change_for_current_month(goal.goal_id)
        recommended_payment = goal.calculate_recommended_payment(
            net_change_this_month=net_change,
        )
        days_left = goal.days_left

        response = api_schemas.GoalResponse.model_validate(goal)

        return response.model_copy(
            update={
                "days_left": days_left,
                "recommended_payment": recommended_payment,
            },
        )

    async def _apply_goal_changes(
        self,
        user_id: UUID,
        goal_id: UUID,
        goal: models.Goal,
        changes_for_db: dict,
    ) -> models.Goal:
        """Применяет изменения цели и обрабатывает смену finish_date."""
        updated_goal = await self.uow.goals.update_fields(
            user_id,
            goal_id,
            changes_for_db,
        )

        if "finish_date" not in changes_for_db:
            return updated_goal

        await self.uow.goals.reset_notification_state(goal_id)

        if (
            updated_goal.status == GoalStatus.EXPIRED.value
            and updated_goal.finish_date
            and updated_goal.finish_date > _get_utc_today()
        ):
            return await self.uow.goals.update_fields(
                user_id,
                goal_id,
                {"status": GoalStatus.ONGOING.value},
            )

        return updated_goal

    async def _check_and_process_achievement_in_uow(
        self,
        goal: models.Goal,
    ) -> bool:
        """Проверяет достижение цели внутри UnitOfWork."""
        if goal.check_achievement():
            await self._process_achieved_goal_in_uow(goal)
            return True

        if goal.revert_achievement_if_needed():
            logger.info("Goal %s reverted to ONGOING", goal.goal_id)
            return True

        return await self._add_almost_achieved_notification_in_uow(goal)

    async def _process_achieved_goal_in_uow(self, goal: models.Goal) -> None:
        """Добавляет события достижения цели."""
        self.uow.outbox.add_event(
            topic=settings.KAFKA.KAFKA_TOPIC_BUDGET_NOTIFICATION,
            payload=_create_outbox_event(
                GoalEventType.ALERT,
                goal_id=str(goal.goal_id),
                days_left=0,
            ),
        )

        await self._add_goal_notification_event(
            "goal.achieved",
            goal,
            {
                "goal_id": str(goal.goal_id),
                "name": goal.name,
            },
        )

        metrics.GOAL_ACHIEVEMENT_TIME.observe(
            (datetime.now(timezone.utc) - goal.created_at).total_seconds(),
        )

    async def _process_expired_goals(self, today: date) -> None:
        """Обрабатывает цели с истекшим сроком."""
        last_id: UUID | None = None

        while True:
            async with self.uow:
                batch = await self.uow.goals.get_expired_goals_batch(
                    today=today,
                    limit=DEADLINE_BATCH_SIZE,
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

                    outbox_events.extend(self._build_expired_goal_events(goal))
                    expired_goal_ids.append(goal.goal_id)

                if outbox_events:
                    self.uow.outbox.add_events(outbox_events)

                if expired_goal_ids:
                    await self.uow.goals.bulk_update_status(
                        expired_goal_ids,
                        GoalStatus.EXPIRED.value,
                    )

    async def _process_approaching_goals(self, today: date) -> None:
        """Обрабатывает цели с приближающимся сроком."""
        while True:
            async with self.uow:
                approaching_batch = await self.uow.goals.get_approaching_goals_batch(
                    today,
                    limit=DEADLINE_BATCH_SIZE,
                )

                if not approaching_batch:
                    break

                outbox_events: list[dict] = []
                checked_ids: list[UUID] = []

                for goal in approaching_batch:
                    outbox_events.extend(self._build_approaching_goal_events(goal))
                    checked_ids.append(goal.goal_id)

                if outbox_events:
                    self.uow.outbox.add_events(outbox_events)

                if checked_ids:
                    await self.uow.goals.update_last_checked(checked_ids)

    async def _check_missed_monthly_payments(
        self,
        today: date,
        batch_size: int,
    ) -> None:
        """Проверяет цели без income-пополнений за прошлый месяц."""
        if today.day != 1:
            return

        period_start, period_end, month_key = _previous_month_period(today)
        last_id: UUID | None = None

        while True:
            async with self.uow:
                batch = await self.uow.goals.get_goals_without_income_batch(
                    period_start=period_start,
                    period_end=period_end,
                    limit=batch_size,
                    last_id=last_id,
                )

                if not batch:
                    break

                last_id = batch[-1].goal_id
                outbox_events = [
                    {
                        "topic": settings.KAFKA.KAFKA_TOPIC_NOTIFICATION_EVENTS,
                        "payload": _create_notification_event(
                            "goal.payment_missed",
                            goal.user_id,
                            {
                                "goal_id": str(goal.goal_id),
                                "name": goal.name,
                            },
                            event_id=_notification_event_id(
                                "goal.payment_missed",
                                goal.goal_id,
                                month_key,
                            ),
                        ),
                    }
                    for goal in batch
                ]

                self.uow.outbox.add_events(outbox_events)

    async def _add_almost_achieved_notification_in_uow(
        self,
        goal: models.Goal,
    ) -> bool:
        """Добавляет notification-событие, если цель почти достигнута."""
        if goal.status != GoalStatus.ONGOING.value:
            return False

        current_percent = _goal_current_percent(goal)
        if current_percent < ALMOST_ACHIEVED_PERCENT:
            return False

        await self._add_goal_notification_event(
            "goal.almost_achieved",
            goal,
            {
                "goal_id": str(goal.goal_id),
                "name": goal.name,
            },
        )

        return True

    async def _add_goal_notification_event(
        self,
        event_name: str,
        goal: models.Goal,
        payload: dict,
    ) -> None:
        """Добавляет событие для notification service в outbox."""
        self.uow.outbox.add_event(
            topic=settings.KAFKA.KAFKA_TOPIC_NOTIFICATION_EVENTS,
            payload=_create_notification_event(
                event_name,
                goal.user_id,
                payload,
                event_id=_notification_event_id(event_name, goal.goal_id),
            ),
        )

    def _add_goal_created_events(self, goal: models.Goal, user_id: UUID) -> None:
        """Добавляет outbox-события создания цели."""
        self.uow.outbox.add_event(
            topic=settings.KAFKA.KAFKA_TOPIC_BUDGET_EVENTS,
            payload=_create_outbox_event(
                GoalEventType.CREATED,
                goal_id=str(goal.goal_id),
                user_id=str(user_id),
                name=goal.name,
                target_amount=goal.target_amount,
                finish_date=goal.finish_date,
                priority=goal.priority,
            ),
        )

        self.uow.outbox.add_event(
            topic=settings.KAFKA.KAFKA_TOPIC_NOTIFICATION_EVENTS,
            payload=_create_notification_event(
                "goal.created",
                user_id,
                {
                    "goal_id": str(goal.goal_id),
                    "name": goal.name,
                    "recommended_payment": _goal_recommended_payment(goal),
                },
                event_id=_notification_event_id("goal.created", goal.goal_id),
            ),
        )

    def _add_goal_changed_event(self, goal_id: UUID, changes: dict) -> None:
        """Добавляет outbox-событие изменения цели."""
        self.uow.outbox.add_event(
            topic=settings.KAFKA.KAFKA_TOPIC_BUDGET_EVENTS,
            payload=_create_outbox_event(
                GoalEventType.CHANGED,
                goal_id=str(goal_id),
                changes=changes,
            ),
        )

    def _add_goal_updated_event(self, goal: models.Goal) -> None:
        """Добавляет outbox-событие обновления баланса цели."""
        self.uow.outbox.add_event(
            topic=settings.KAFKA.KAFKA_TOPIC_BUDGET_EVENTS,
            payload=_create_outbox_event(
                GoalEventType.UPDATED,
                goal_id=str(goal.goal_id),
                current_amount=goal.current_amount,
                status=goal.status,
            ),
        )

    def _build_expired_goal_events(self, goal: models.Goal) -> list[dict]:
        """Формирует outbox-события истечения цели."""
        return [
            {
                "topic": settings.KAFKA.KAFKA_TOPIC_BUDGET_EVENTS,
                "payload": _create_outbox_event(
                    GoalEventType.UPDATED,
                    goal_id=str(goal.goal_id),
                    status=GoalStatus.EXPIRED.value,
                ),
            },
            {
                "topic": settings.KAFKA.KAFKA_TOPIC_BUDGET_NOTIFICATION,
                "payload": _create_outbox_event(
                    GoalEventType.EXPIRED,
                    goal_id=str(goal.goal_id),
                    days_left=0,
                ),
            },
            {
                "topic": settings.KAFKA.KAFKA_TOPIC_NOTIFICATION_EVENTS,
                "payload": _create_notification_event(
                    "goal.expired",
                    goal.user_id,
                    {
                        "goal_id": str(goal.goal_id),
                        "name": goal.name,
                    },
                    event_id=_notification_event_id("goal.expired", goal.goal_id),
                ),
            },
        ]

    def _build_approaching_goal_events(self, goal: models.Goal) -> list[dict]:
        """Формирует outbox-события приближения срока цели."""
        return [
            {
                "topic": settings.KAFKA.KAFKA_TOPIC_BUDGET_NOTIFICATION,
                "payload": _create_outbox_event(
                    GoalEventType.APPROACHING,
                    goal_id=str(goal.goal_id),
                    type="approaching",
                    days_left=goal.days_left,
                ),
            },
            {
                "topic": settings.KAFKA.KAFKA_TOPIC_NOTIFICATION_EVENTS,
                "payload": _create_notification_event(
                    "goal.deadline_approaching",
                    goal.user_id,
                    {
                        "goal_id": str(goal.goal_id),
                        "name": goal.name,
                        "days_left": goal.days_left,
                        "current_percent": _goal_current_percent(goal),
                    },
                    event_id=_notification_event_id(
                        "goal.deadline_approaching",
                        goal.goal_id,
                    ),
                ),
            },
        ]

    @staticmethod
    def _validate_finish_date(finish_date: date | None) -> None:
        """Проверяет, что finish_date находится в будущем."""
        if finish_date and finish_date <= _get_utc_today():
            raise exceptions.InvalidGoalDataError("Finish date must be in the future")

    @staticmethod
    def _prepare_goal_changes(update_data: dict) -> tuple[dict, dict]:
        """Подготавливает изменения цели для БД и Kafka."""
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

        return changes_for_db, changes_for_kafka

    @staticmethod
    def _resolve_restored_status(goal: models.Goal) -> GoalStatus:
        """Определяет статус цели при восстановлении."""
        today = _get_utc_today()

        if goal.finish_date and goal.finish_date < today:
            return GoalStatus.EXPIRED

        if goal.current_amount >= goal.target_amount:
            return GoalStatus.ACHIEVED

        return GoalStatus.ONGOING
