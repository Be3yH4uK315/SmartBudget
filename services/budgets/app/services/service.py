import logging
from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

from sqlalchemy.exc import IntegrityError

from app.core import config, exceptions
from app.domain.enums import TransactionType
from app.domain.schemas import api as api_schemas
from app.domain.schemas import kafka as kafka_schemas
from app.infrastructure.db import models
from app.infrastructure.db.uow import UnitOfWork

logger = logging.getLogger(__name__)
settings = config.settings


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _current_month_start() -> date:
    now = _utc_now()
    return date(now.year, now.month, 1)


def _month_start(value: date | datetime | None = None) -> date:
    if value is None:
        return _current_month_start()
    if isinstance(value, datetime):
        value = value.astimezone(timezone.utc) if value.tzinfo else value
    return date(value.year, value.month, 1)


def _previous_month_start(month: date) -> date:
    if month.month == 1:
        return date(month.year - 1, 12, 1)
    return date(month.year, month.month - 1, 1)


def _expense_total(budget: models.Budget) -> Decimal:
    return sum(
        (
            category.spent_amount
            for category in budget.category_limits
            if category.spent_amount > 0
        ),
        Decimal("0.00"),
    )


def _category_expense(category: models.CategoryLimit | None) -> Decimal:
    if category is None or category.spent_amount <= 0:
        return Decimal("0.00")
    return category.spent_amount


def _threshold_crossed(
    limit: Decimal,
    before: Decimal,
    after: Decimal,
    ratio: Decimal,
) -> bool:
    if limit <= 0:
        return False
    boundary = limit * ratio
    return before < boundary <= after


def _request_limit_amount(
    request: api_schemas.CategoryLimitRequest | api_schemas.PatchCategoryLimitRequest,
) -> Decimal:
    return request.limit_amount


def _request_total_limit_amount(
    request: api_schemas.CreateBudgetRequest | api_schemas.PatchBudgetRequest,
) -> Decimal | None:
    return request.total_limit_amount


def _category_response(category: models.CategoryLimit) -> api_schemas.CategoryResponse:
    return api_schemas.CategoryResponse(
        category_id=category.category_id,
        limit_amount=category.limit_amount,
        spent_amount=category.spent_amount,
    )


def _category_settings_response(
    category: models.CategoryLimit,
) -> api_schemas.CategorySettingsResponse:
    return api_schemas.CategorySettingsResponse(
        category_id=category.category_id,
        limit_amount=category.limit_amount,
    )


def _budget_to_response(budget: models.Budget) -> api_schemas.BudgetResponse:
    categories = sorted(budget.category_limits, key=lambda item: item.category_id)
    return api_schemas.BudgetResponse(
        total_limit_amount=budget.total_limit_amount,
        spent_amount=_expense_total(budget),
        is_auto_renew=budget.is_auto_renew,
        categories=[_category_response(category) for category in categories],
    )


def _budget_to_settings_response(
    budget: models.Budget,
) -> api_schemas.BudgetSettingsResponse:
    categories = sorted(
        (
            category
            for category in budget.category_limits
            if category.limit_amount != Decimal("0.00")
        ),
        key=lambda item: item.category_id,
    )
    return api_schemas.BudgetSettingsResponse(
        total_limit_amount=budget.total_limit_amount,
        is_auto_renew=budget.is_auto_renew,
        categories=[
            _category_settings_response(category)
            for category in categories
        ],
    )


def _budget_to_dashboard_response(
    budget: models.Budget,
) -> api_schemas.DashboardBudgetResponse:
    categories = []
    for category in sorted(budget.category_limits, key=lambda item: item.category_id):
        categories.append(
            api_schemas.DashboardCategoryResponse(
                category_id=category.category_id,
                amount=category.spent_amount,
                transaction_type="expense",
            )
        )

    return api_schemas.DashboardBudgetResponse(
        categories=categories,
        total_limit_amount=budget.total_limit_amount,
    )


def _budget_event(
    event_type: str,
    user_id: UUID,
    details: dict,
) -> dict:
    return kafka_schemas.BudgetEventMessage(
        event_type=event_type,
        user_id=user_id,
        details=details,
    ).model_dump(mode="json", by_alias=True, exclude_none=True)


def _notification_event_id(event_name: str, key: str) -> UUID:
    return uuid5(NAMESPACE_URL, f"smartbudget:notifications:{event_name}:{key}")


def _notification_event(
    event_name: str,
    user_id: UUID,
    payload: dict[str, object],
    event_id: UUID,
) -> dict:
    return kafka_schemas.NotificationEvent(
        event_id=event_id,
        event_type=event_name,
        user_id=user_id,
        payload=payload,
        timestamp=_utc_now(),
    ).model_dump(mode="json", by_alias=True, exclude_none=True)


def _budget_notification_key(
    budget: models.Budget,
    event_name: str,
    suffix: str,
) -> str:
    month = budget.month.strftime("%Y-%m")
    return f"{budget.budget_id}:{month}:{event_name}:{suffix}"


def _ensure_unique_categories(categories) -> None:
    category_ids = [category.category_id for category in categories]
    if len(category_ids) != len(set(category_ids)):
        raise exceptions.InvalidBudgetDataError("Duplicate category limits are not allowed")


class BudgetService:
    """Сервис для управления бюджетом пользователя."""

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def _queue_notification(
        self,
        event_name: str,
        user_id: UUID,
        payload: dict[str, object],
        key: str,
    ) -> None:
        self.uow.outbox.add_event(
            topic=settings.KAFKA.KAFKA_TOPIC_NOTIFICATION_EVENTS,
            payload=_notification_event(
                event_name,
                user_id,
                payload,
                event_id=_notification_event_id(event_name, key),
            ),
            event_type=event_name,
        )

    def _queue_threshold_notifications(
        self,
        user_id: UUID,
        budget: models.Budget,
        total_before: Decimal,
        category: models.CategoryLimit | None,
        category_before: Decimal,
    ) -> None:
        total_after = _expense_total(budget)
        if _threshold_crossed(
            budget.total_limit_amount,
            total_before,
            total_after,
            Decimal("0.80"),
        ):
            percent = int((total_after / budget.total_limit_amount) * 100)
            self._queue_notification(
                "budget.total.reached_80",
                user_id,
                {"percent": percent},
                _budget_notification_key(budget, "budget.total.reached_80", "total"),
            )
        if _threshold_crossed(
            budget.total_limit_amount,
            total_before,
            total_after,
            Decimal("1.00"),
        ):
            self._queue_notification(
                "budget.total.exceeded",
                user_id,
                {},
                _budget_notification_key(budget, "budget.total.exceeded", "total"),
            )

        if not category:
            return

        category_after = _category_expense(category)
        if _threshold_crossed(
            category.limit_amount,
            category_before,
            category_after,
            Decimal("0.80"),
        ):
            self._queue_notification(
                "budget.limit.reached_80",
                user_id,
                {"category_id": category.category_id},
                _budget_notification_key(
                    budget,
                    "budget.limit.reached_80",
                    str(category.category_id),
                ),
            )
        if _threshold_crossed(
            category.limit_amount,
            category_before,
            category_after,
            Decimal("1.00"),
        ):
            self._queue_notification(
                "budget.limit.exceeded",
                user_id,
                {"category_id": category.category_id},
                _budget_notification_key(
                    budget,
                    "budget.limit.exceeded",
                    str(category.category_id),
                ),
            )

    def _apply_patch_to_existing_budget(
        self,
        budget: models.Budget,
        request: api_schemas.PatchBudgetRequest,
        now: datetime,
    ) -> None:
        total_limit_amount = _request_total_limit_amount(request)
        if total_limit_amount is not None:
            budget.total_limit_amount = total_limit_amount

        if request.is_auto_renew is not None:
            budget.is_auto_renew = request.is_auto_renew

        if request.categories is not None:
            incoming_by_category = {
                category.category_id: category
                for category in request.categories
            }

            for existing in budget.category_limits:
                incoming = incoming_by_category.get(existing.category_id)
                existing.limit_amount = (
                    _request_limit_amount(incoming)
                    if incoming is not None
                    else Decimal("0.00")
                )
                existing.updated_at = now

            existing_category_ids = {
                category.category_id
                for category in budget.category_limits
            }

            for incoming in request.categories:
                if incoming.category_id in existing_category_ids:
                    continue
                budget.category_limits.append(
                    models.CategoryLimit(
                        category_limit_id=uuid4(),
                        budget_id=budget.budget_id,
                        category_id=incoming.category_id,
                        limit_amount=_request_limit_amount(incoming),
                        spent_amount=Decimal("0.00"),
                        created_at=now,
                        updated_at=now,
                    )
                )

        budget.updated_at = now

    async def get_budget(
        self,
        user_id: UUID,
        target_date: date | None = None,
    ) -> api_schemas.BudgetResponse:
        async with self.uow:
            budget = await self.uow.budgets.get_by_user_month(
                user_id,
                _month_start(target_date),
            )
            if not budget:
                return api_schemas.BudgetResponse(
                    total_limit_amount=Decimal("0.00"),
                    spent_amount=Decimal("0.00"),
                    is_auto_renew=False,
                    categories=[],
                )
            return _budget_to_response(budget)

    async def get_budget_settings(
        self,
        user_id: UUID,
        target_date: date | None = None,
    ) -> api_schemas.BudgetSettingsResponse:
        async with self.uow:
            budget = await self.uow.budgets.get_by_user_month(
                user_id,
                _month_start(target_date),
            )
            if not budget:
                return api_schemas.BudgetSettingsResponse(
                    total_limit_amount=Decimal("0.00"),
                    is_auto_renew=False,
                    categories=[],
                )
            return _budget_to_settings_response(budget)

    async def get_dashboard_budget(
        self,
        user_id: UUID,
        target_date: date | None = None,
    ) -> api_schemas.DashboardBudgetResponse:
        async with self.uow:
            budget = await self.uow.budgets.get_by_user_month(
                user_id,
                _month_start(target_date),
            )
            if not budget:
                return api_schemas.DashboardBudgetResponse(
                    categories=[],
                    total_limit_amount=Decimal("0.00"),
                )
            return _budget_to_dashboard_response(budget)

    async def create_budget(
        self,
        user_id: UUID,
        request: api_schemas.CreateBudgetRequest,
        target_date: date | None = None,
    ) -> str:
        _ensure_unique_categories(request.categories)
        now = _utc_now()
        budget_id = uuid4()
        month = _month_start(target_date)
        total_limit_amount = _request_total_limit_amount(request) or Decimal("0.00")
        budget = models.Budget(
            budget_id=budget_id,
            user_id=user_id,
            month=month,
            total_income_amount=Decimal("0.00"),
            total_limit_amount=total_limit_amount,
            is_auto_renew=request.is_auto_renew,
            created_at=now,
            updated_at=now,
        )
        budget.category_limits = [
            models.CategoryLimit(
                category_limit_id=uuid4(),
                budget_id=budget_id,
                category_id=category.category_id,
                limit_amount=_request_limit_amount(category),
                spent_amount=Decimal("0.00"),
                created_at=now,
                updated_at=now,
            )
            for category in request.categories
        ]

        try:
            async with self.uow:
                existing = await self.uow.budgets.get_by_user_month_for_update(
                    user_id,
                    month,
                )
                if existing:
                    raise exceptions.BudgetAlreadyExistsError("Budget already exists")

                self.uow.budgets.create(budget)
                self.uow.outbox.add_event(
                    topic=settings.KAFKA.KAFKA_TOPIC_BUDGET_EVENTS,
                    payload=_budget_event(
                        "budget.created",
                        user_id,
                        {
                            "budget_id": str(budget_id),
                            "total_limit_amount": budget.total_limit_amount,
                            "is_auto_renew": budget.is_auto_renew,
                        },
                    ),
                    event_type="budget.created",
                )
        except IntegrityError as exc:
            raise exceptions.BudgetAlreadyExistsError("Budget already exists") from exc

        return str(budget_id)

    async def patch_budget(
        self,
        user_id: UUID,
        request: api_schemas.PatchBudgetRequest,
        target_date: date | None = None,
    ) -> None:
        if request.categories is not None:
            _ensure_unique_categories(request.categories)

        try:
            async with self.uow:
                month = _month_start(target_date)
                budget = await self.uow.budgets.get_by_user_id_for_update(
                    user_id,
                    month,
                )
                now = _utc_now()
                created = False

                if not budget:
                    created = True
                    total_limit_amount = (
                        _request_total_limit_amount(request)
                        or Decimal("0.00")
                    )
                    budget = models.Budget(
                        budget_id=uuid4(),
                        user_id=user_id,
                        month=month,
                        total_income_amount=Decimal("0.00"),
                        total_limit_amount=total_limit_amount,
                        is_auto_renew=request.is_auto_renew or False,
                        created_at=now,
                        updated_at=now,
                    )
                    budget.category_limits = [
                        models.CategoryLimit(
                            category_limit_id=uuid4(),
                            budget_id=budget.budget_id,
                            category_id=category.category_id,
                            limit_amount=_request_limit_amount(category),
                            spent_amount=Decimal("0.00"),
                            created_at=now,
                            updated_at=now,
                        )
                        for category in (request.categories or [])
                    ]
                    self.uow.budgets.create(budget)
                else:
                    self._apply_patch_to_existing_budget(budget, request, now)

                if created:
                    self.uow.outbox.add_event(
                        topic=settings.KAFKA.KAFKA_TOPIC_BUDGET_EVENTS,
                        payload=_budget_event(
                            "budget.created",
                            user_id,
                            {
                                "budget_id": str(budget.budget_id),
                                "total_limit_amount": budget.total_limit_amount,
                                "is_auto_renew": budget.is_auto_renew,
                            },
                        ),
                        event_type="budget.created",
                    )

                self.uow.outbox.add_event(
                    topic=settings.KAFKA.KAFKA_TOPIC_BUDGET_EVENTS,
                    payload=_budget_event(
                        "budget.settings_changed",
                        user_id,
                        {
                            "budget_id": str(budget.budget_id),
                            "total_limit_amount": budget.total_limit_amount,
                            "is_auto_renew": budget.is_auto_renew,
                        },
                    ),
                    event_type="budget.settings_changed",
                )
                self.uow.outbox.add_event(
                    topic=settings.KAFKA.KAFKA_TOPIC_NOTIFICATION_EVENTS,
                    payload=_notification_event(
                        "budget.settings.changed",
                        user_id,
                        {"budget_id": str(budget.budget_id)},
                        event_id=_notification_event_id(
                            "budget.settings.changed",
                            str(budget.budget_id),
                        ),
                    ),
                    event_type="budget.settings.changed",
                )
        except IntegrityError:
            logger.info(
                "Budget settings upsert conflicted, retrying as update",
                extra={"user_id": str(user_id), "target_date": str(target_date)},
            )
            async with self.uow:
                month = _month_start(target_date)
                budget = await self.uow.budgets.get_by_user_id_for_update(
                    user_id,
                    month,
                )
                if not budget:
                    raise exceptions.InvalidBudgetDataError(
                        "Budget settings update conflict"
                    )
                now = _utc_now()
                self._apply_patch_to_existing_budget(budget, request, now)
                self.uow.outbox.add_event(
                    topic=settings.KAFKA.KAFKA_TOPIC_BUDGET_EVENTS,
                    payload=_budget_event(
                        "budget.settings_changed",
                            user_id,
                            {
                                "budget_id": str(budget.budget_id),
                                "total_limit_amount": budget.total_limit_amount,
                                "is_auto_renew": budget.is_auto_renew,
                            },
                    ),
                    event_type="budget.settings_changed",
                )
                self._queue_notification(
                    "budget.settings.changed",
                    user_id,
                    {"budget_id": str(budget.budget_id)},
                    str(budget.budget_id),
                )

    async def renew_monthly_budgets(
        self,
        target_date: date | None = None,
        batch_size: int = 500,
    ) -> int:
        """Создает бюджеты текущего месяца из настроек auto-renew прошлого месяца."""
        target_month = _month_start(target_date)
        previous_month = _previous_month_start(target_month)
        now = _utc_now()
        created_count = 0

        async with self.uow:
            candidates = await self.uow.budgets.list_auto_renew_budgets(
                previous_month,
                batch_size,
            )
            for previous in candidates:
                existing = await self.uow.budgets.get_by_user_month_for_update(
                    previous.user_id,
                    target_month,
                )
                if existing:
                    continue

                budget_id = uuid4()
                budget = models.Budget(
                    budget_id=budget_id,
                    user_id=previous.user_id,
                    month=target_month,
                    total_income_amount=Decimal("0.00"),
                    total_limit_amount=previous.total_limit_amount,
                    is_auto_renew=previous.is_auto_renew,
                    created_at=now,
                    updated_at=now,
                )
                budget.category_limits = [
                    models.CategoryLimit(
                        category_limit_id=uuid4(),
                        budget_id=budget_id,
                        category_id=category.category_id,
                        limit_amount=category.limit_amount,
                        spent_amount=Decimal("0.00"),
                        created_at=now,
                        updated_at=now,
                    )
                    for category in previous.category_limits
                    if category.limit_amount > Decimal("0.00")
                ]
                self.uow.budgets.create(budget)
                self.uow.outbox.add_event(
                    topic=settings.KAFKA.KAFKA_TOPIC_BUDGET_EVENTS,
                    payload=_budget_event(
                        "budget.created",
                        previous.user_id,
                        {
                            "budget_id": str(budget_id),
                            "total_limit_amount": budget.total_limit_amount,
                            "is_auto_renew": budget.is_auto_renew,
                            "month": target_month.isoformat(),
                            "source": "auto_renew",
                        },
                    ),
                    event_type="budget.created",
                )
                created_count += 1

        return created_count

    async def process_new_transaction(
        self,
        message: kafka_schemas.TransactionNewMessage,
    ) -> None:
        if message.category_id is None:
            return

        occurred_at = message.occurred_at or _utc_now()
        month = _month_start(occurred_at)
        async with self.uow:
            if message.transaction_id:
                processed = await self.uow.budgets.get_processed_transaction(
                    message.transaction_id,
                )
                if processed:
                    logger.info(
                        "Budget transaction already processed",
                        extra={"transaction_id": str(message.transaction_id)},
                    )
                    return

            budget = await self.uow.budgets.get_by_user_id_for_update(
                message.user_id,
                month,
            )
            if not budget:
                logger.warning("Budget not found for user %s", message.user_id)
                return

            total_before = _expense_total(budget)
            target_category = self.uow.budgets.get_or_create_category(
                budget,
                message.category_id,
            )
            category_before = _category_expense(target_category)
            updated_category = self.uow.budgets.adjust_category_spent(
                budget,
                message.category_id,
                message.amount,
                message.transaction_type,
            )
            self._queue_threshold_notifications(
                message.user_id,
                budget,
                total_before,
                updated_category,
                category_before,
            )

            if message.transaction_id:
                self.uow.budgets.add_processed_transaction(
                    transaction_id=message.transaction_id,
                    user_id=message.user_id,
                    month=month,
                    category_id=message.category_id,
                    amount=message.amount,
                    transaction_type=message.transaction_type,
                    occurred_at=occurred_at,
                )

    async def process_updated_transaction(
        self,
        message: kafka_schemas.TransactionUpdatedMessage,
    ) -> None:
        async with self.uow:
            processed = await self.uow.budgets.get_processed_transaction(
                message.transaction_id,
            )

            user_id = message.user_id or (processed.user_id if processed else None)
            if user_id is None:
                logger.warning(
                    "Cannot update budget transaction without user context",
                    extra={"transaction_id": str(message.transaction_id)},
                )
                return

            occurred_at = message.occurred_at or (
                processed.occurred_at if processed else _utc_now()
            )
            new_month = _month_start(occurred_at)
            old_month = processed.month if processed else new_month
            old_budget = await self.uow.budgets.get_by_user_id_for_update(
                user_id,
                old_month,
            )
            if not old_budget:
                logger.warning("Budget not found for user %s", user_id)
                return

            budget = old_budget
            if new_month != old_month:
                budget = await self.uow.budgets.get_by_user_id_for_update(
                    user_id,
                    new_month,
                )
                if not budget:
                    logger.warning("Budget not found for user %s", user_id)
                    return

            total_before = _expense_total(budget)
            target_category = (
                self.uow.budgets.get_or_create_category(
                    budget,
                    message.new_category_id,
                )
                if message.new_category_id is not None
                else None
            )
            category_before = _category_expense(target_category)

            if processed:
                self.uow.budgets.adjust_category_spent(
                    old_budget,
                    processed.category_id,
                    processed.amount,
                    TransactionType(processed.transaction_type),
                    multiplier=-1,
                )
            else:
                self.uow.budgets.adjust_category_spent(
                    old_budget,
                    message.old_category_id,
                    message.amount,
                    message.transaction_type,
                    multiplier=-1,
                )

            self.uow.budgets.adjust_category_spent(
                budget,
                message.new_category_id,
                message.amount,
                message.transaction_type,
            )
            self._queue_threshold_notifications(
                user_id,
                budget,
                total_before,
                target_category,
                category_before,
            )

            if processed:
                processed.user_id = user_id
                processed.month = new_month
                processed.category_id = message.new_category_id
                processed.amount = message.amount
                processed.transaction_type = message.transaction_type.value
                processed.occurred_at = occurred_at
                processed.updated_at = _utc_now()
            else:
                self.uow.budgets.add_processed_transaction(
                    transaction_id=message.transaction_id,
                    user_id=user_id,
                    month=new_month,
                    category_id=message.new_category_id,
                    amount=message.amount,
                    transaction_type=message.transaction_type,
                    occurred_at=occurred_at,
                )

    async def process_deleted_transaction(
        self,
        message: kafka_schemas.TransactionDeletedMessage,
    ) -> None:
        async with self.uow:
            processed = await self.uow.budgets.get_processed_transaction(
                message.transaction_id,
            )
            if not processed:
                logger.info(
                    "Budget transaction delete ignored: transaction was not processed",
                    extra={"transaction_id": str(message.transaction_id)},
                )
                return

            user_id = message.user_id or processed.user_id
            budget = await self.uow.budgets.get_by_user_id_for_update(
                user_id,
                processed.month,
            )
            if not budget:
                logger.warning("Budget not found for user %s", user_id)
                return

            self.uow.budgets.adjust_category_spent(
                budget,
                processed.category_id,
                processed.amount,
                TransactionType(processed.transaction_type),
                multiplier=-1,
            )
            await self.uow.budgets.delete_processed_transaction(
                message.transaction_id,
            )
