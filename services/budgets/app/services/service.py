import logging
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

from sqlalchemy.exc import IntegrityError

from app.core import config, exceptions
from app.domain.enums import TransactionType
from app.domain.schemas import api as api_schemas
from app.domain.schemas import kafka as kafka_schemas
from smartbudget_shared.events import (
    BudgetEventType,
    BudgetPayload,
    EventEnvelope,
    EventSource,
    NotificationPayload,
)
from app.infrastructure.db import models
from app.infrastructure.db.uow import UnitOfWork

logger = logging.getLogger(__name__)
settings = config.settings

BUDGET_PRE_OVERFLOW_RATIO = Decimal("0.80")
BUDGET_OVERFLOW_RATIO = Decimal("1.00")
ZERO_AMOUNT = Decimal("0.00")


def _utc_now() -> datetime:
    """Возвращает текущее UTC-время."""
    return datetime.now(timezone.utc)


def _current_month_start() -> date:
    """Возвращает первое число текущего месяца."""
    now = _utc_now()
    return date(now.year, now.month, 1)


def _month_start(value: date | datetime | None = None) -> date:
    """Возвращает первое число месяца для даты или datetime."""
    if value is None:
        return _current_month_start()

    if isinstance(value, datetime):
        value = value.astimezone(timezone.utc) if value.tzinfo else value

    return date(value.year, value.month, 1)


def _previous_month_start(month: date) -> date:
    """Возвращает первое число предыдущего месяца."""
    if month.month == 1:
        return date(month.year - 1, 12, 1)

    return date(month.year, month.month - 1, 1)


def _expense_total(budget: models.Budget) -> Decimal:
    """Считает общую сумму расходов по бюджету."""
    return sum(
        (
            category.spent_amount
            for category in budget.category_limits
            if category.spent_amount > 0
        ),
        ZERO_AMOUNT,
    )


def _category_expense(category: models.CategoryLimit | None) -> Decimal:
    """Возвращает расход категории."""
    if category is None or category.spent_amount <= 0:
        return ZERO_AMOUNT

    return category.spent_amount


def _threshold_crossed(
    limit: Decimal,
    before: Decimal,
    after: Decimal,
    ratio: Decimal,
) -> bool:
    """Проверяет пересечение порога лимита."""
    if limit <= 0:
        return False

    boundary = limit * ratio

    return before < boundary <= after


def _request_limit_amount(
    request: api_schemas.CategoryLimitRequest | api_schemas.PatchCategoryLimitRequest,
) -> Decimal:
    """Возвращает limit_amount из request-модели."""
    return request.limit_amount


def _request_total_limit_amount(
    request: api_schemas.CreateBudgetRequest | api_schemas.PatchBudgetRequest,
) -> Decimal | None:
    """Возвращает total_limit_amount из request-модели."""
    return request.total_limit_amount


def _category_response(category: models.CategoryLimit) -> api_schemas.CategoryResponse:
    """Преобразует CategoryLimit в API response."""
    return api_schemas.CategoryResponse(
        category_id=category.category_id,
        limit_amount=category.limit_amount,
        spent_amount=category.spent_amount,
    )


def _category_settings_response(
    category: models.CategoryLimit,
) -> api_schemas.CategorySettingsResponse:
    """Преобразует CategoryLimit в response настроек."""
    return api_schemas.CategorySettingsResponse(
        category_id=category.category_id,
        limit_amount=category.limit_amount,
    )


def _budget_to_response(budget: models.Budget) -> api_schemas.BudgetResponse:
    """Преобразует Budget в основной API response."""
    categories = sorted(
        budget.category_limits,
        key=lambda item: item.category_id,
    )

    return api_schemas.BudgetResponse(
        total_limit_amount=budget.total_limit_amount,
        spent_amount=_expense_total(budget),
        is_auto_renew=budget.is_auto_renew,
        categories=[
            _category_response(category)
            for category in categories
        ],
    )


def _budget_to_settings_response(
    budget: models.Budget,
) -> api_schemas.BudgetSettingsResponse:
    """Преобразует Budget в response настроек."""
    categories = sorted(
        (
            category
            for category in budget.category_limits
            if category.limit_amount != ZERO_AMOUNT
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
    """Преобразует Budget в response для главного экрана."""
    categories = [
        api_schemas.DashboardCategoryResponse(
            category_id=category.category_id,
            amount=category.spent_amount,
            transaction_type="expense",
        )
        for category in sorted(
            budget.category_limits,
            key=lambda item: item.category_id,
        )
    ]

    return api_schemas.DashboardBudgetResponse(
        categories=categories,
        total_limit_amount=budget.total_limit_amount,
    )


def _budget_event(
    event_type: str,
    user_id: UUID,
    details: dict[str, Any],
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    """Создает budget event envelope."""
    payload = BudgetPayload(
        budget_id=UUID(str(details["budget_id"])) if details.get("budget_id") else None,
        user_id=user_id,
        details=details,
    )
    event = EventEnvelope.create(
        event_type=event_type,
        source_service=EventSource.BUDGETS,
        payload=payload,
        idempotency_key=idempotency_key,
    )

    return event.model_dump(
        mode="json",
        by_alias=True,
        exclude_none=True,
    )


def _notification_event_id(event_name: str, key: str) -> UUID:
    """Создает детерминированный notification event id."""
    return uuid5(NAMESPACE_URL, f"smartbudget:notifications:{event_name}:{key}")


def _notification_event(
    event_name: str,
    user_id: UUID,
    payload: dict[str, Any],
    event_id: UUID,
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    """Создает notification event envelope."""
    event_payload = NotificationPayload(
        user_id=user_id,
        payload=payload,
    )
    event = EventEnvelope.create(
        event_id=event_id,
        event_type=event_name,
        source_service=EventSource.BUDGETS,
        payload=event_payload,
        occurred_at=_utc_now(),
        idempotency_key=idempotency_key,
    )

    return event.model_dump(
        mode="json",
        by_alias=True,
        exclude_none=True,
    )


def _budget_notification_key(
    budget: models.Budget,
    event_name: str,
    suffix: str,
) -> str:
    """Создает ключ идемпотентности notification-события бюджета."""
    month = budget.month.strftime("%Y-%m")

    return f"{budget.budget_id}:{month}:{event_name}:{suffix}"


def _ensure_unique_categories(categories) -> None:
    """Проверяет, что категории в request не дублируются."""
    category_ids = [
        category.category_id
        for category in categories
    ]

    if len(category_ids) != len(set(category_ids)):
        raise exceptions.InvalidBudgetDataError(
            "Duplicate category limits are not allowed",
        )


class BudgetService:
    """Сервис управления бюджетами пользователя."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def get_budget(
        self,
        user_id: UUID,
        target_date: date | None = None,
    ) -> api_schemas.BudgetResponse:
        """Возвращает бюджет пользователя за месяц."""
        async with self.uow:
            budget = await self.uow.budgets.get_by_user_month(
                user_id,
                _month_start(target_date),
            )

            if not budget:
                return self._empty_budget_response()

            return _budget_to_response(budget)

    async def get_budget_settings(
        self,
        user_id: UUID,
        target_date: date | None = None,
    ) -> api_schemas.BudgetSettingsResponse:
        """Возвращает настройки бюджета пользователя за месяц."""
        async with self.uow:
            budget = await self.uow.budgets.get_by_user_month(
                user_id,
                _month_start(target_date),
            )

            if not budget:
                return self._empty_budget_settings_response()

            return _budget_to_settings_response(budget)

    async def get_dashboard_budget(
        self,
        user_id: UUID,
        target_date: date | None = None,
    ) -> api_schemas.DashboardBudgetResponse:
        """Возвращает бюджет для главного экрана."""
        async with self.uow:
            budget = await self.uow.budgets.get_by_user_month(
                user_id,
                _month_start(target_date),
            )

            if not budget:
                return self._empty_dashboard_budget_response()

            return _budget_to_dashboard_response(budget)

    async def create_budget(
        self,
        user_id: UUID,
        request: api_schemas.CreateBudgetRequest,
        target_date: date | None = None,
    ) -> str:
        """Создает бюджет пользователя."""
        _ensure_unique_categories(request.categories)

        now = _utc_now()
        budget_id = uuid4()
        month = _month_start(target_date)

        budget = self._build_budget(
            budget_id=budget_id,
            user_id=user_id,
            month=month,
            total_limit_amount=_request_total_limit_amount(request) or ZERO_AMOUNT,
            is_auto_renew=request.is_auto_renew,
            now=now,
        )
        budget.category_limits = self._build_category_limits(
            budget_id=budget_id,
            categories=request.categories,
            now=now,
        )

        try:
            async with self.uow:
                existing = await self.uow.budgets.get_by_user_month_for_update(
                    user_id,
                    month,
                )
                if existing:
                    raise exceptions.BudgetAlreadyExistsError("Budget already exists")

                self.uow.budgets.create(budget)
                self._queue_budget_created_event(
                    user_id=user_id,
                    budget=budget,
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
        """Создает или обновляет настройки бюджета пользователя."""
        if request.categories is not None:
            _ensure_unique_categories(request.categories)

        try:
            async with self.uow:
                budget, created = await self._get_or_create_budget_for_patch(
                    user_id=user_id,
                    request=request,
                    target_date=target_date,
                )

                if created:
                    self._queue_budget_created_event(
                        user_id=user_id,
                        budget=budget,
                    )

                self._queue_budget_settings_changed_events(
                    user_id=user_id,
                    budget=budget,
                )

        except IntegrityError:
            await self._retry_patch_after_integrity_error(
                user_id=user_id,
                request=request,
                target_date=target_date,
            )

    async def renew_monthly_budgets(
        self,
        target_date: date | None = None,
        batch_size: int = 500,
    ) -> int:
        """Создает бюджеты текущего месяца из auto-renew бюджетов прошлого месяца."""
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

                budget = self._build_renewed_budget(
                    previous=previous,
                    target_month=target_month,
                    now=now,
                )

                self.uow.budgets.create(budget)
                self._queue_budget_created_event(
                    user_id=previous.user_id,
                    budget=budget,
                    extra_details={
                        "month": target_month.isoformat(),
                        "source": "auto_renew",
                    },
                )
                created_count += 1

        return created_count

    async def process_new_transaction(
        self,
        message: kafka_schemas.TransactionNewMessage,
    ) -> None:
        """Обрабатывает новую транзакцию из Kafka."""
        if message.category_id is None:
            return

        occurred_at = message.occurred_at or _utc_now()
        month = _month_start(occurred_at)

        async with self.uow:
            if await self._transaction_already_processed(message.transaction_id):
                return

            budget = await self.uow.budgets.get_by_user_id_for_update(
                message.user_id,
                month,
            )
            if not budget:
                logger.warning("Budget not found for user %s", message.user_id)
                return

            self._apply_new_transaction_to_budget(
                user_id=message.user_id,
                budget=budget,
                category_id=message.category_id,
                amount=message.amount,
                transaction_type=message.transaction_type,
            )

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
        """Обрабатывает обновление транзакции из Kafka."""
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

            self._apply_updated_transaction_to_budget(
                user_id=user_id,
                budget=budget,
                old_budget=old_budget,
                processed=processed,
                message=message,
            )

            if processed:
                self._update_processed_transaction(
                    processed=processed,
                    user_id=user_id,
                    new_month=new_month,
                    message=message,
                    occurred_at=occurred_at,
                )
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
        """Обрабатывает удаление транзакции из Kafka."""
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

    def _queue_notification(
        self,
        event_name: str,
        user_id: UUID,
        payload: dict[str, Any],
        key: str,
    ) -> None:
        """Добавляет notification event в outbox."""
        self.uow.outbox.add_event(
            topic=settings.KAFKA.KAFKA_TOPIC_NOTIFICATION_EVENTS,
            payload=_notification_event(
                event_name,
                user_id,
                payload,
                event_id=_notification_event_id(event_name, key),
                idempotency_key=f"{event_name}:{key}",
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
        """Добавляет notification events при пересечении бюджетных порогов."""
        total_after = _expense_total(budget)

        self._queue_total_threshold_notifications(
            user_id=user_id,
            budget=budget,
            total_before=total_before,
            total_after=total_after,
        )

        if not category:
            return

        self._queue_category_threshold_notifications(
            user_id=user_id,
            budget=budget,
            category=category,
            category_before=category_before,
        )

    def _queue_total_threshold_notifications(
        self,
        user_id: UUID,
        budget: models.Budget,
        total_before: Decimal,
        total_after: Decimal,
    ) -> None:
        """Добавляет уведомления по общему лимиту бюджета."""
        if _threshold_crossed(
            budget.total_limit_amount,
            total_before,
            total_after,
            BUDGET_PRE_OVERFLOW_RATIO,
        ):
            percent = int((total_after / budget.total_limit_amount) * 100)
            self._queue_notification(
                "budget.total.reached_80",
                user_id,
                {"percent": percent},
                _budget_notification_key(
                    budget,
                    "budget.total.reached_80",
                    "total",
                ),
            )

        if _threshold_crossed(
            budget.total_limit_amount,
            total_before,
            total_after,
            BUDGET_OVERFLOW_RATIO,
        ):
            self._queue_notification(
                "budget.total.exceeded",
                user_id,
                {},
                _budget_notification_key(
                    budget,
                    "budget.total.exceeded",
                    "total",
                ),
            )

    def _queue_category_threshold_notifications(
        self,
        user_id: UUID,
        budget: models.Budget,
        category: models.CategoryLimit,
        category_before: Decimal,
    ) -> None:
        """Добавляет уведомления по лимиту категории."""
        category_after = _category_expense(category)

        if _threshold_crossed(
            category.limit_amount,
            category_before,
            category_after,
            BUDGET_PRE_OVERFLOW_RATIO,
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
            BUDGET_OVERFLOW_RATIO,
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

    def _queue_budget_created_event(
        self,
        user_id: UUID,
        budget: models.Budget,
        extra_details: dict[str, Any] | None = None,
    ) -> None:
        """Добавляет budget.created event в outbox."""
        details = {
            "budget_id": str(budget.budget_id),
            "total_limit_amount": budget.total_limit_amount,
            "is_auto_renew": budget.is_auto_renew,
        }

        if extra_details:
            details.update(extra_details)

        event_type = BudgetEventType.BUDGET_CREATED.value

        self.uow.outbox.add_event(
            topic=settings.KAFKA.KAFKA_TOPIC_BUDGET_EVENTS,
            payload=_budget_event(
                event_type,
                user_id,
                details,
                idempotency_key=f"{event_type}:{budget.budget_id}",
            ),
            event_type=event_type,
        )

    def _queue_budget_settings_changed_events(
        self,
        user_id: UUID,
        budget: models.Budget,
    ) -> None:
        """Добавляет события изменения настроек бюджета."""
        budget_event_type = "budget.settings_changed"
        notification_event_type = "budget.settings.changed"

        self.uow.outbox.add_event(
            topic=settings.KAFKA.KAFKA_TOPIC_BUDGET_EVENTS,
            payload=_budget_event(
                budget_event_type,
                user_id,
                {
                    "budget_id": str(budget.budget_id),
                    "total_limit_amount": budget.total_limit_amount,
                    "is_auto_renew": budget.is_auto_renew,
                },
                idempotency_key=f"{budget_event_type}:{budget.budget_id}",
            ),
            event_type=budget_event_type,
        )
        self.uow.outbox.add_event(
            topic=settings.KAFKA.KAFKA_TOPIC_NOTIFICATION_EVENTS,
            payload=_notification_event(
                notification_event_type,
                user_id,
                {"budget_id": str(budget.budget_id)},
                event_id=_notification_event_id(
                    notification_event_type,
                    str(budget.budget_id),
                ),
                idempotency_key=f"{notification_event_type}:{budget.budget_id}",
            ),
            event_type=notification_event_type,
        )

    def _apply_patch_to_existing_budget(
        self,
        budget: models.Budget,
        request: api_schemas.PatchBudgetRequest,
        now: datetime,
    ) -> None:
        """Применяет patch request к существующему бюджету."""
        total_limit_amount = _request_total_limit_amount(request)
        if total_limit_amount is not None:
            budget.total_limit_amount = total_limit_amount

        if request.is_auto_renew is not None:
            budget.is_auto_renew = request.is_auto_renew

        if request.categories is not None:
            self._apply_category_limits_patch(
                budget=budget,
                categories=request.categories,
                now=now,
            )

        budget.updated_at = now

    def _apply_category_limits_patch(
        self,
        budget: models.Budget,
        categories: list[api_schemas.PatchCategoryLimitRequest],
        now: datetime,
    ) -> None:
        """Применяет изменения лимитов категорий."""
        incoming_by_category = {
            category.category_id: category
            for category in categories
        }

        for existing in budget.category_limits:
            incoming = incoming_by_category.get(existing.category_id)
            existing.limit_amount = (
                _request_limit_amount(incoming)
                if incoming is not None
                else ZERO_AMOUNT
            )
            existing.updated_at = now

        existing_category_ids = {
            category.category_id
            for category in budget.category_limits
        }

        for incoming in categories:
            if incoming.category_id in existing_category_ids:
                continue

            budget.category_limits.append(
                models.CategoryLimit(
                    category_limit_id=uuid4(),
                    budget_id=budget.budget_id,
                    category_id=incoming.category_id,
                    limit_amount=_request_limit_amount(incoming),
                    spent_amount=ZERO_AMOUNT,
                    created_at=now,
                    updated_at=now,
                ),
            )

    async def _get_or_create_budget_for_patch(
        self,
        user_id: UUID,
        request: api_schemas.PatchBudgetRequest,
        target_date: date | None,
    ) -> tuple[models.Budget, bool]:
        """Получает бюджет для patch или создает новый."""
        month = _month_start(target_date)
        budget = await self.uow.budgets.get_by_user_id_for_update(
            user_id,
            month,
        )
        now = _utc_now()

        if budget:
            self._apply_patch_to_existing_budget(budget, request, now)
            return budget, False

        budget = self._build_budget(
            budget_id=uuid4(),
            user_id=user_id,
            month=month,
            total_limit_amount=_request_total_limit_amount(request) or ZERO_AMOUNT,
            is_auto_renew=request.is_auto_renew or False,
            now=now,
        )
        budget.category_limits = self._build_category_limits(
            budget_id=budget.budget_id,
            categories=request.categories or [],
            now=now,
        )

        self.uow.budgets.create(budget)

        return budget, True

    async def _retry_patch_after_integrity_error(
        self,
        user_id: UUID,
        request: api_schemas.PatchBudgetRequest,
        target_date: date | None,
    ) -> None:
        """Повторяет patch как update после конфликта уникальности."""
        logger.info(
            "Budget settings upsert conflicted, retrying as update",
            extra={
                "user_id": str(user_id),
                "target_date": str(target_date),
            },
        )

        async with self.uow:
            month = _month_start(target_date)
            budget = await self.uow.budgets.get_by_user_id_for_update(
                user_id,
                month,
            )

            if not budget:
                raise exceptions.InvalidBudgetDataError(
                    "Budget settings update conflict",
                )

            self._apply_patch_to_existing_budget(
                budget,
                request,
                _utc_now(),
            )
            self._queue_budget_settings_changed_events(
                user_id=user_id,
                budget=budget,
            )

    def _apply_new_transaction_to_budget(
        self,
        user_id: UUID,
        budget: models.Budget,
        category_id: int,
        amount: Decimal,
        transaction_type: TransactionType,
    ) -> None:
        """Применяет новую транзакцию к бюджету."""
        total_before = _expense_total(budget)
        target_category = self.uow.budgets.get_or_create_category(
            budget,
            category_id,
        )
        category_before = _category_expense(target_category)

        updated_category = self.uow.budgets.adjust_category_spent(
            budget,
            category_id,
            amount,
            transaction_type,
        )

        self._queue_threshold_notifications(
            user_id,
            budget,
            total_before,
            updated_category,
            category_before,
        )

    def _apply_updated_transaction_to_budget(
        self,
        user_id: UUID,
        budget: models.Budget,
        old_budget: models.Budget,
        processed: models.ProcessedBudgetTransaction | None,
        message: kafka_schemas.TransactionUpdatedMessage,
    ) -> None:
        """Применяет обновление транзакции к бюджету."""
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

    async def _transaction_already_processed(self, transaction_id: UUID) -> bool:
        """Проверяет идемпотентность обработки транзакции."""
        processed = await self.uow.budgets.get_processed_transaction(transaction_id)

        if not processed:
            return False

        logger.info(
            "Budget transaction already processed",
            extra={"transaction_id": str(transaction_id)},
        )

        return True

    @staticmethod
    def _update_processed_transaction(
        processed: models.ProcessedBudgetTransaction,
        user_id: UUID,
        new_month: date,
        message: kafka_schemas.TransactionUpdatedMessage,
        occurred_at: datetime,
    ) -> None:
        """Обновляет запись обработанной транзакции."""
        processed.user_id = user_id
        processed.month = new_month
        processed.category_id = message.new_category_id
        processed.amount = message.amount
        processed.transaction_type = message.transaction_type.value
        processed.occurred_at = occurred_at
        processed.updated_at = _utc_now()

    @staticmethod
    def _build_budget(
        budget_id: UUID,
        user_id: UUID,
        month: date,
        total_limit_amount: Decimal,
        is_auto_renew: bool,
        now: datetime,
    ) -> models.Budget:
        """Создает ORM-модель бюджета."""
        return models.Budget(
            budget_id=budget_id,
            user_id=user_id,
            month=month,
            total_income_amount=ZERO_AMOUNT,
            total_limit_amount=total_limit_amount,
            is_auto_renew=is_auto_renew,
            created_at=now,
            updated_at=now,
        )

    @staticmethod
    def _build_category_limits(
        budget_id: UUID,
        categories: list[
            api_schemas.CategoryLimitRequest | api_schemas.PatchCategoryLimitRequest
        ],
        now: datetime,
    ) -> list[models.CategoryLimit]:
        """Создает ORM-модели лимитов категорий."""
        return [
            models.CategoryLimit(
                category_limit_id=uuid4(),
                budget_id=budget_id,
                category_id=category.category_id,
                limit_amount=_request_limit_amount(category),
                spent_amount=ZERO_AMOUNT,
                created_at=now,
                updated_at=now,
            )
            for category in categories
        ]

    @staticmethod
    def _build_renewed_budget(
        previous: models.Budget,
        target_month: date,
        now: datetime,
    ) -> models.Budget:
        """Создает бюджет нового месяца на основе auto-renew бюджета прошлого месяца."""
        budget_id = uuid4()
        budget = BudgetService._build_budget(
            budget_id=budget_id,
            user_id=previous.user_id,
            month=target_month,
            total_limit_amount=previous.total_limit_amount,
            is_auto_renew=previous.is_auto_renew,
            now=now,
        )
        budget.category_limits = [
            models.CategoryLimit(
                category_limit_id=uuid4(),
                budget_id=budget_id,
                category_id=category.category_id,
                limit_amount=category.limit_amount,
                spent_amount=ZERO_AMOUNT,
                created_at=now,
                updated_at=now,
            )
            for category in previous.category_limits
            if category.limit_amount > ZERO_AMOUNT
        ]

        return budget

    @staticmethod
    def _empty_budget_response() -> api_schemas.BudgetResponse:
        """Возвращает пустой budget response."""
        return api_schemas.BudgetResponse(
            total_limit_amount=ZERO_AMOUNT,
            spent_amount=ZERO_AMOUNT,
            is_auto_renew=False,
            categories=[],
        )

    @staticmethod
    def _empty_budget_settings_response() -> api_schemas.BudgetSettingsResponse:
        """Возвращает пустой settings response."""
        return api_schemas.BudgetSettingsResponse(
            total_limit_amount=ZERO_AMOUNT,
            is_auto_renew=False,
            categories=[],
        )

    @staticmethod
    def _empty_dashboard_budget_response() -> api_schemas.DashboardBudgetResponse:
        """Возвращает пустой dashboard response."""
        return api_schemas.DashboardBudgetResponse(
            categories=[],
            total_limit_amount=ZERO_AMOUNT,
        )
