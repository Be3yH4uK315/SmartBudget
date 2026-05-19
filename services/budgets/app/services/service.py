import logging
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError

from app.core import config, exceptions
from app.domain.enums import TransactionType
from app.domain.schemas import api as api_schemas
from smartbudget_shared.events import (
    BudgetEventType,
    BudgetPayload,
    TransactionCategoryUpdatedPayload,
    TransactionClassifiedPayload,
    TransactionDeletedPayload,
    TransactionPayload,
    TransactionUpdatedPayload,
    create_budget_event,
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


def _income_total(budget: models.Budget) -> Decimal:
    """Считает общую сумму доходов по бюджету."""
    return sum(
        (
            category.income_amount
            for category in budget.category_limits
            if category.income_amount > 0
        ),
        ZERO_AMOUNT,
    )


def _category_expense(category: models.CategoryLimit | None) -> Decimal:
    """Возвращает расход категории."""
    if category is None or category.spent_amount <= 0:
        return ZERO_AMOUNT

    return category.spent_amount


def _budget_total_exceeded_count(budget: models.Budget) -> int:
    """Возвращает 1, если общий бюджет превышен."""
    if budget.total_limit_amount <= 0:
        return 0

    return int(_expense_total(budget) > budget.total_limit_amount)


def _budget_category_exceeded_count(budget: models.Budget) -> int:
    """Считает количество превышенных категорий."""
    return sum(
        1
        for category in budget.category_limits
        if category.limit_amount > 0 and _category_expense(category) > category.limit_amount
    )


def _percent_used(spent_amount: Decimal, limit_amount: Decimal | None) -> int:
    """Считает процент использования лимита."""
    if not limit_amount or limit_amount <= 0:
        return 0

    return int((spent_amount / limit_amount * Decimal("100")).quantize(Decimal("1")))


def _threshold_crossed(
    limit_amount: Decimal,
    before: Decimal,
    after: Decimal,
    ratio: Decimal,
) -> bool:
    """Проверяет пересечение порога лимита."""
    if limit_amount <= 0:
        return False

    boundary = limit_amount * ratio

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


def _budget_transaction_type(
    category_id: int | None,
    transaction_type: TransactionType | str,
) -> TransactionType:
    """Возвращает тип транзакции с точки зрения бюджета."""
    resolved_type = (
        transaction_type
        if isinstance(transaction_type, TransactionType)
        else TransactionType(transaction_type)
    )

    if category_id != settings.APP.GOAL_CATEGORY_ID:
        return resolved_type

    if resolved_type == TransactionType.INCOME:
        return TransactionType.EXPENSE

    return TransactionType.INCOME


def _category_response(category: models.CategoryLimit) -> api_schemas.CategoryResponse:
    """Преобразует CategoryLimit в API response."""
    return api_schemas.CategoryResponse(
        category_id=category.category_id,
        limit_amount=category.limit_amount,
        spent_amount=category.spent_amount,
        income_amount=category.income_amount,
    )


def _budget_category_responses(
    categories: list[models.CategoryLimit],
) -> list[api_schemas.BudgetCategoryResponse]:
    """Преобразует категории в агрегаты по типу транзакции."""
    result: list[api_schemas.BudgetCategoryResponse] = []

    for category in sorted(categories, key=lambda item: item.category_id):
        result.append(
            api_schemas.BudgetCategoryResponse(
                category_id=category.category_id,
                limit_amount=category.limit_amount,
                amount=category.spent_amount,
                transaction_type=TransactionType.EXPENSE,
            ),
        )
        result.append(
            api_schemas.BudgetCategoryResponse(
                category_id=category.category_id,
                limit_amount=ZERO_AMOUNT,
                amount=category.income_amount,
                transaction_type=TransactionType.INCOME,
            ),
        )

    return sorted(
        result,
        key=lambda item: (-item.amount, item.category_id, item.transaction_type.value),
    )


def _category_settings_response(
    category: models.CategoryLimit,
) -> api_schemas.CategorySettingsResponse:
    """Преобразует CategoryLimit в response настроек."""
    return api_schemas.CategorySettingsResponse(
        category_id=category.category_id,
        limit_amount=category.limit_amount,
        income_amount=category.income_amount,
    )


def _budget_to_response(budget: models.Budget) -> api_schemas.BudgetResponse:
    """Преобразует Budget в основной API response."""
    return api_schemas.BudgetResponse(
        budget_id=budget.budget_id,
        total_limit_amount=budget.total_limit_amount,
        total_income_amount=_income_total(budget),
        total_spent_amount=_expense_total(budget),
        is_auto_renew=budget.is_auto_renew,
        categories=_budget_category_responses(list(budget.category_limits)),
    )


def _budget_to_create_response(
    budget: models.Budget,
) -> api_schemas.CreateBudgetResponse:
    """Преобразует Budget в response создания бюджета."""
    categories = sorted(
        budget.category_limits,
        key=lambda item: item.category_id,
    )

    return api_schemas.CreateBudgetResponse(
        budget_id=budget.budget_id,
        total_limit_amount=budget.total_limit_amount,
        total_income_amount=_income_total(budget),
        total_spent_amount=_expense_total(budget),
        is_auto_renew=budget.is_auto_renew,
        categories=[_category_response(category) for category in categories],
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
        categories=[_category_settings_response(category) for category in categories],
    )


def _budget_to_dashboard_response(
    budget: models.Budget,
) -> api_schemas.DashboardBudgetResponse:
    """Преобразует Budget в response для главного экрана."""
    return api_schemas.DashboardBudgetResponse(
        categories=_budget_category_responses(list(budget.category_limits)),
        total_limit_amount=budget.total_limit_amount,
        total_income_amount=_income_total(budget),
    )


def _budget_event(
    event_type: BudgetEventType | str,
    user_id: UUID,
    budget: models.Budget,
    category: models.CategoryLimit | None = None,
    threshold_percent: int | None = None,
) -> dict[str, Any]:
    """Создает budget event envelope."""
    is_category_event = category is not None

    limit_amount = category.limit_amount if is_category_event else budget.total_limit_amount
    spent_amount = _category_expense(category) if is_category_event else _expense_total(budget)

    payload = BudgetPayload(
        budget_id=budget.budget_id,
        user_id=user_id,
        category_id=category.category_id if category else None,
        limit_amount=limit_amount,
        spent_amount=spent_amount,
        percent=_percent_used(spent_amount, limit_amount),
        threshold_percent=threshold_percent,
        checked_at=_utc_now()
        if event_type == BudgetEventType.BUDGET_CHECK_RESULTS
        else None,
        total_exceeded_count=_budget_total_exceeded_count(budget)
        if event_type == BudgetEventType.BUDGET_CHECK_RESULTS
        else None,
        category_exceeded_count=_budget_category_exceeded_count(budget)
        if event_type == BudgetEventType.BUDGET_CHECK_RESULTS
        else None,
    )
    event = create_budget_event(
        event_type=event_type,
        payload=payload,
    )

    return event.model_dump(
        mode="json",
        by_alias=True,
        exclude_none=True,
    )


def _ensure_unique_categories(categories) -> None:
    """Проверяет, что категории в request не дублируются."""
    category_ids = [category.category_id for category in categories]

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
    ) -> api_schemas.CreateBudgetResponse:
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

                return _budget_to_create_response(budget)

        except IntegrityError as exc:
            raise exceptions.BudgetAlreadyExistsError("Budget already exists") from exc


    async def patch_budget(
        self,
        user_id: UUID,
        request: api_schemas.PatchBudgetRequest,
        target_date: date | None = None,
    ) -> api_schemas.PatchBudgetResponse:
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

                return api_schemas.PatchBudgetResponse(
                    budget_id=budget.budget_id,
                    updated=True,
                )

        except IntegrityError:
            return await self._retry_patch_after_integrity_error(
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

    async def backfill_transactions(
        self,
        user_id: UUID,
        request: api_schemas.BackfillBudgetTransactionsRequest,
        target_date: date | None = None,
    ) -> api_schemas.BackfillBudgetTransactionsResponse:
        """Восстанавливает бюджетную статистику по переданным транзакциям."""
        target_month = _month_start(target_date) if target_date else None
        applied_count = 0
        skipped_count = 0

        async with self.uow:
            for item in request.transactions:
                category_id = item.category_id
                if category_id is None and item.account_id is not None:
                    category_id = settings.APP.GOAL_CATEGORY_ID

                if category_id is None:
                    skipped_count += 1
                    continue

                transaction_month = _month_start(item.date)
                if target_month and transaction_month != target_month:
                    skipped_count += 1
                    continue

                if await self._transaction_already_processed(item.transaction_id):
                    skipped_count += 1
                    continue

                budget = await self.uow.budgets.get_by_user_id_for_update(
                    user_id,
                    transaction_month,
                )
                if not budget:
                    logger.warning(
                        "Budget not found for backfill",
                        extra={
                            "user_id": str(user_id),
                            "month": transaction_month.isoformat(),
                        },
                    )
                    skipped_count += 1
                    continue

                budget_transaction_type = _budget_transaction_type(
                    category_id,
                    item.transaction_type,
                )

                self._apply_new_transaction_to_budget(
                    user_id=user_id,
                    budget=budget,
                    category_id=category_id,
                    amount=item.amount,
                    transaction_type=budget_transaction_type,
                )

                self.uow.budgets.add_processed_transaction(
                    transaction_id=item.transaction_id,
                    user_id=user_id,
                    month=transaction_month,
                    category_id=category_id,
                    amount=item.amount,
                    transaction_type=budget_transaction_type,
                    date=item.date,
                )
                applied_count += 1

        return api_schemas.BackfillBudgetTransactionsResponse(
            applied_count=applied_count,
            skipped_count=skipped_count,
        )

    async def process_new_transaction(
        self,
        message: TransactionPayload,
    ) -> None:
        """Обрабатывает новую транзакцию из Kafka."""
        if message.category_id is None:
            return

        date = message.date or _utc_now()
        month = _month_start(date)

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

            budget_transaction_type = _budget_transaction_type(
                message.category_id,
                message.transaction_type,
            )

            self._apply_new_transaction_to_budget(
                user_id=message.user_id,
                budget=budget,
                category_id=message.category_id,
                amount=message.amount,
                transaction_type=budget_transaction_type,
            )

            self.uow.budgets.add_processed_transaction(
                transaction_id=message.transaction_id,
                user_id=message.user_id,
                month=month,
                category_id=message.category_id,
                amount=message.amount,
                transaction_type=budget_transaction_type,
                date=date,
            )

    async def process_updated_transaction(
        self,
        message: (
            TransactionUpdatedPayload
            | TransactionClassifiedPayload
            | TransactionCategoryUpdatedPayload
        ),
    ) -> None:
        """Обрабатывает обновление транзакции из Kafka."""
        async with self.uow:
            resolved_category_id = (
                message.new_category_id
                if hasattr(message, "new_category_id")
                else message.category_id
            )

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

            date = message.date or (
                processed.date if processed else _utc_now()
            )
            new_month = _month_start(date)
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

            budget_transaction_type = _budget_transaction_type(
                resolved_category_id,
                message.transaction_type,
            )

            self._apply_updated_transaction_to_budget(
                user_id=user_id,
                budget=budget,
                old_budget=old_budget,
                processed=processed,
                message=message,
                category_id=resolved_category_id,
                transaction_type=budget_transaction_type,
            )

            if processed:
                self._update_processed_transaction(
                    processed=processed,
                    user_id=user_id,
                    new_month=new_month,
                    category_id=resolved_category_id,
                    amount=message.amount,
                    transaction_type=budget_transaction_type,
                    date=date,
                )
            else:
                self.uow.budgets.add_processed_transaction(
                    transaction_id=message.transaction_id,
                    user_id=user_id,
                    month=new_month,
                    category_id=resolved_category_id,
                    amount=message.amount,
                    transaction_type=budget_transaction_type,
                    date=date,
                )

    async def process_deleted_transaction(
        self,
        message: TransactionDeletedPayload,
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

    def _queue_budget_created_event(
        self,
        user_id: UUID,
        budget: models.Budget,
        extra_details: dict[str, Any] | None = None,
    ) -> None:
        """Добавляет budget.created event в outbox."""
        event_type = BudgetEventType.BUDGET_CREATED

        self.uow.outbox.add_event(
            topic=settings.KAFKA.KAFKA_TOPIC_BUDGET_EVENTS,
            payload=_budget_event(
                event_type=event_type,
                user_id=user_id,
                budget=budget,
            ),
            event_type=event_type.value,
        )

    def _queue_budget_settings_changed_events(
        self,
        user_id: UUID,
        budget: models.Budget,
    ) -> None:
        """Добавляет budget.settings.changed event при изменении настроек бюджета."""
        event_type = BudgetEventType.BUDGET_SETTINGS_CHANGED

        self.uow.outbox.add_event(
            topic=settings.KAFKA.KAFKA_TOPIC_BUDGET_EVENTS,
            payload=_budget_event(
                event_type=event_type,
                user_id=user_id,
                budget=budget,
            ),
            event_type=event_type.value,
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
            category.category_id: category for category in categories
        }

        for existing in budget.category_limits:
            incoming = incoming_by_category.get(existing.category_id)
            existing.limit_amount = (
                _request_limit_amount(incoming) if incoming is not None else ZERO_AMOUNT
            )
            existing.updated_at = now

        existing_category_ids = {
            category.category_id for category in budget.category_limits
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
                    income_amount=ZERO_AMOUNT,
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
    ) -> api_schemas.PatchBudgetResponse:
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

            return api_schemas.PatchBudgetResponse(
                budget_id=budget.budget_id,
                updated=True,
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

        self._queue_threshold_events(
            user_id=user_id,
            budget=budget,
            total_before=total_before,
            category=updated_category,
            category_before=category_before,
        )

    def _apply_updated_transaction_to_budget(
        self,
        user_id: UUID,
        budget: models.Budget,
        old_budget: models.Budget,
        processed: models.ProcessedBudgetTransaction | None,
        message: (
            TransactionUpdatedPayload
            | TransactionClassifiedPayload
            | TransactionCategoryUpdatedPayload
        ),
        category_id: int | None,
        transaction_type: TransactionType,
    ) -> None:
        """Применяет обновление транзакции к бюджету."""
        total_before = _expense_total(budget)
        target_category = (
            self.uow.budgets.get_or_create_category(
                budget,
                category_id,
            )
            if category_id is not None
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
            old_category_id = getattr(message, "old_category_id", None)
            old_transaction_type = _budget_transaction_type(
                old_category_id,
                message.transaction_type,
            )
            self.uow.budgets.adjust_category_spent(
                old_budget,
                old_category_id,
                message.amount,
                old_transaction_type,
                multiplier=-1,
            )

        self.uow.budgets.adjust_category_spent(
            budget,
            category_id,
            message.amount,
            transaction_type,
        )
        self._queue_threshold_events(
            user_id=user_id,
            budget=budget,
            total_before=total_before,
            category=target_category,
            category_before=category_before,
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

    def _queue_threshold_events(
        self,
        user_id: UUID,
        budget: models.Budget,
        total_before: Decimal,
        category: models.CategoryLimit | None,
        category_before: Decimal,
    ) -> None:
        """Добавляет budget.threshold_reached events при пересечении порогов."""
        total_after = _expense_total(budget)

        self._queue_total_threshold_events(
            user_id=user_id,
            budget=budget,
            total_before=total_before,
            total_after=total_after,
        )

        if not category:
            return

        self._queue_category_threshold_events(
            user_id=user_id,
            budget=budget,
            category=category,
            category_before=category_before,
        )

    def _queue_total_threshold_events(
        self,
        user_id: UUID,
        budget: models.Budget,
        total_before: Decimal,
        total_after: Decimal,
    ) -> None:
        """Добавляет события по общему лимиту бюджета."""
        if _threshold_crossed(
            budget.total_limit_amount,
            total_before,
            total_after,
            BUDGET_PRE_OVERFLOW_RATIO,
        ):
            self._queue_total_budget_event(
                user_id=user_id,
                budget=budget,
                event_type=BudgetEventType.BUDGET_TOTAL_THRESHOLD_REACHED,
                threshold_percent=80,
            )

        if _threshold_crossed(
            budget.total_limit_amount,
            total_before,
            total_after,
            BUDGET_OVERFLOW_RATIO,
        ):
            self._queue_total_budget_event(
                user_id=user_id,
                budget=budget,
                event_type=BudgetEventType.BUDGET_TOTAL_EXCEEDED,
                threshold_percent=100,
            )

    def _queue_category_threshold_events(
        self,
        user_id: UUID,
        budget: models.Budget,
        category: models.CategoryLimit,
        category_before: Decimal,
    ) -> None:
        """Добавляет события по лимиту категории."""
        category_after = _category_expense(category)

        if _threshold_crossed(
            category.limit_amount,
            category_before,
            category_after,
            BUDGET_PRE_OVERFLOW_RATIO,
        ):
            self._queue_category_budget_event(
                user_id=user_id,
                budget=budget,
                category=category,
                event_type=BudgetEventType.BUDGET_CATEGORY_THRESHOLD_REACHED,
                threshold_percent=80,
            )

        if _threshold_crossed(
            category.limit_amount,
            category_before,
            category_after,
            BUDGET_OVERFLOW_RATIO,
        ):
            self._queue_category_budget_event(
                user_id=user_id,
                budget=budget,
                category=category,
                event_type=BudgetEventType.BUDGET_CATEGORY_EXCEEDED,
                threshold_percent=100,
            )

    def _queue_total_budget_event(
        self,
        user_id: UUID,
        budget: models.Budget,
        event_type: BudgetEventType,
        threshold_percent: int | None = None,
    ) -> None:
        """Добавляет событие по общему бюджету в outbox."""
        self.uow.outbox.add_event(
            topic=settings.KAFKA.KAFKA_TOPIC_BUDGET_EVENTS,
            payload=_budget_event(
                event_type=event_type,
                user_id=user_id,
                budget=budget,
                threshold_percent=threshold_percent,
            ),
            event_type=event_type.value,
        )

    def _queue_category_budget_event(
        self,
        user_id: UUID,
        budget: models.Budget,
        category: models.CategoryLimit,
        event_type: BudgetEventType,
        threshold_percent: int | None = None,
    ) -> None:
        """Добавляет событие по лимиту категории в outbox."""
        self.uow.outbox.add_event(
            topic=settings.KAFKA.KAFKA_TOPIC_BUDGET_EVENTS,
            payload=_budget_event(
                event_type=event_type,
                user_id=user_id,
                budget=budget,
                category=category,
                threshold_percent=threshold_percent,
            ),
            event_type=event_type.value,
        )

    @staticmethod
    def _update_processed_transaction(
        processed: models.ProcessedBudgetTransaction,
        user_id: UUID,
        new_month: date,
        category_id: int | None,
        amount: Decimal,
        transaction_type: TransactionType,
        date: datetime,
    ) -> None:
        """Обновляет запись обработанной транзакции."""
        processed.user_id = user_id
        processed.month = new_month
        processed.category_id = category_id
        processed.amount = amount
        processed.transaction_type = transaction_type.value
        processed.date = date
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
                income_amount=ZERO_AMOUNT,
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
                income_amount=ZERO_AMOUNT,
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
            budget_id=None,
            total_limit_amount=ZERO_AMOUNT,
            total_income_amount=ZERO_AMOUNT,
            total_spent_amount=ZERO_AMOUNT,
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
            total_income_amount=ZERO_AMOUNT,
        )
