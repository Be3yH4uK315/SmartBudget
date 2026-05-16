import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from app.core import exceptions
from app.core.config import settings
from app.domain import enums
from app.domain.schemas import api as api_schemas
from app.infrastructure.db import models
from app.infrastructure.db.uow import UnitOfWork
from smartbudget_shared.events import (
    TransactionCategoryChangedPayload,
    TransactionDeletedPayload,
    TransactionGoalAppliedPayload,
    TransactionNeedCategoryPayload,
    TransactionPayload,
    TransactionUpdatedPayload,
    create_transaction_category_changed_event,
    create_transaction_created_event,
    create_transaction_deleted_event,
    create_transaction_goal_applied_event,
    create_transaction_need_category_event,
    create_transaction_updated_event,
)

logger = logging.getLogger(__name__)

EMPTY_UUID = UUID("00000000-0000-0000-0000-000000000000")


def _utc_now() -> datetime:
    """Возвращает текущее UTC-время."""
    return datetime.now(timezone.utc)


def _ensure_aware(value: datetime | None) -> datetime:
    """Возвращает timezone-aware datetime в UTC."""
    if value is None:
        return _utc_now()

    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def _transaction_amount(transaction: models.Transaction) -> Decimal:
    """Возвращает сумму транзакции."""
    return transaction.amount


def _transaction_type(transaction: models.Transaction) -> enums.TransactionType:
    """Возвращает тип транзакции."""
    return enums.TransactionType(transaction.transaction_type)


def _transaction_status(transaction: models.Transaction) -> enums.TransactionStatus:
    """Возвращает статус транзакции."""
    return enums.TransactionStatus(transaction.status)


def _transaction_occurred_at(transaction: models.Transaction) -> datetime:
    """Возвращает время транзакции в UTC."""
    return _ensure_aware(transaction.date)


def _transaction_event_date(transaction: models.Transaction) -> datetime:
    """Возвращает дату транзакции для событий."""
    return _transaction_occurred_at(transaction)


def _has_goal_account(account_id: UUID | None) -> bool:
    """Проверяет, что транзакция относится к счету цели."""
    return account_id is not None and account_id != EMPTY_UUID


def _goal_transaction_description(
    transaction_type: enums.TransactionType,
) -> str:
    """Возвращает описание операции по цели."""
    if transaction_type == enums.TransactionType.INCOME:
        return "Пополнение цели"

    return "Списание с цели"


def _model_to_api(transaction: models.Transaction) -> api_schemas.TransactionResponse:
    """Преобразует ORM-модель в краткий API response."""
    return api_schemas.TransactionResponse(
        transaction_id=transaction.transaction_id,
        amount=_transaction_amount(transaction),
        category_id=transaction.category_id,
        description=transaction.description,
        merchant=transaction.merchant,
        mcc=transaction.mcc,
        status=_transaction_status(transaction),
        date=_transaction_occurred_at(transaction),
        transaction_type=_transaction_type(transaction),
    )


def _model_to_detail(
    transaction: models.Transaction,
) -> api_schemas.TransactionDetailResponse:
    """Преобразует ORM-модель в детальный API response."""
    return api_schemas.TransactionDetailResponse(
        user_id=transaction.user_id,
        transaction_id=transaction.transaction_id,
        account_id=transaction.account_id,
        category_id=transaction.category_id,
        date=_transaction_occurred_at(transaction),
        amount=_transaction_amount(transaction),
        transaction_type=_transaction_type(transaction),
        status=_transaction_status(transaction),
        merchant=transaction.merchant,
        mcc=transaction.mcc,
        description=transaction.description,
        created_at=transaction.created_at,
        imported_at=transaction.imported_at,
        updated_at=transaction.updated_at,
    )


class TransactionService:
    """Сервис управления транзакциями пользователя."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def list_transactions(
        self,
        user_id: UUID,
        limit_amount: int,
        offset: int,
        category_ids: list[int] | None = None,
        occurred_from: datetime | None = None,
        occurred_to: datetime | None = None,
        transaction_type: enums.TransactionType | None = None,
        amount_from: Decimal | None = None,
        amount_to: Decimal | None = None,
    ) -> list[api_schemas.TransactionResponse]:
        """Возвращает список транзакций пользователя с фильтрацией."""
        async with self.uow:
            transactions = await self.uow.transactions.list_user_transactions(
                user_id=user_id,
                limit_amount=limit_amount,
                offset=offset,
                category_ids=category_ids,
                occurred_from=occurred_from,
                occurred_to=occurred_to,
                transaction_type=transaction_type.value if transaction_type else None,
                amount_from=amount_from,
                amount_to=amount_to,
            )

        return [_model_to_api(transaction) for transaction in transactions]

    async def search_transactions(
        self,
        user_id: UUID,
        query: str,
        limit_amount: int,
    ) -> list[api_schemas.TransactionResponse]:
        """Ищет транзакции пользователя по merchant или description."""
        normalized_query = query.strip()
        if not normalized_query:
            return []

        async with self.uow:
            transactions = await self.uow.transactions.search_user_transactions(
                user_id=user_id,
                query_text=normalized_query,
                limit_amount=limit_amount,
            )

        return [_model_to_api(transaction) for transaction in transactions]

    async def get_transaction(
        self,
        user_id: UUID,
        transaction_id: UUID,
    ) -> api_schemas.TransactionDetailResponse:
        """Возвращает детальную информацию о транзакции."""
        async with self.uow:
            transaction = await self.uow.transactions.get_user_transaction(
                user_id,
                transaction_id,
            )
            if not transaction:
                raise exceptions.TransactionNotFoundError("Transaction not found")

            return _model_to_detail(transaction)

    async def create_manual_transaction(
        self,
        user_id: UUID,
        request: api_schemas.CreateManualTransactionRequest,
    ) -> api_schemas.CreateManualTransactionResponse:
        """Создает ручную транзакцию пользователя."""
        now = _utc_now()
        transaction = self._build_manual_transaction(
            user_id=user_id,
            request=request,
            now=now,
        )

        async with self.uow:
            self.uow.transactions.create(transaction)
            await self.uow.flush()
            self._publish_created_events(transaction)

        return api_schemas.CreateManualTransactionResponse(
            transaction_id=transaction.transaction_id,
        )

    async def import_mock_transactions(
        self,
        request: api_schemas.ImportMockTransactionsRequest,
        request_user_id: UUID | None = None,
    ) -> api_schemas.ImportMockTransactionsResponse:
        """Импортирует mock-транзакции."""
        raw_items = request.root
        items = raw_items if isinstance(raw_items, list) else [raw_items]

        prepared_transactions = self._prepare_import_transactions(
            items=items,
            request_user_id=request_user_id,
        )
        if not prepared_transactions:
            return api_schemas.ImportMockTransactionsResponse(imported_count=0)

        imported_count = 0

        async with self.uow:
            existing_ids = await self.uow.transactions.get_existing_transaction_ids(
                [transaction.transaction_id for transaction in prepared_transactions],
            )

            for transaction in prepared_transactions:
                if transaction.transaction_id in existing_ids:
                    continue

                self.uow.transactions.create(transaction)
                self._publish_imported_events(transaction)
                imported_count += 1

        return api_schemas.ImportMockTransactionsResponse(imported_count=imported_count)

    async def patch_category(
        self,
        user_id: UUID,
        transaction_id: UUID,
        request: api_schemas.PatchTransactionCategoryRequest,
    ) -> api_schemas.PatchTransactionCategoryResponse:
        """Изменяет категорию транзакции пользователя."""
        async with self.uow:
            transaction = await self.uow.transactions.get_user_transaction_for_update(
                user_id,
                transaction_id,
            )
            if not transaction:
                raise exceptions.TransactionNotFoundError("Transaction not found")

            old_category_id = transaction.category_id
            transaction.category_id = request.category_id
            transaction.updated_at = _utc_now()

            await self.uow.flush()

            self._publish_category_changed_events(
                transaction=transaction,
                old_category_id=old_category_id,
                new_category_id=request.category_id,
            )

        return api_schemas.PatchTransactionCategoryResponse(
            transaction_id=transaction_id,
            old_category_id=old_category_id,
            new_category_id=request.category_id,
        )

    async def delete_user_transaction(
        self,
        user_id: UUID,
        transaction_id: UUID,
    ) -> api_schemas.DeleteTransactionResponse:
        """Удаляет транзакцию пользователя."""
        async with self.uow:
            transaction = await self.uow.transactions.delete_user_transaction(
                user_id,
                transaction_id,
            )
            if not transaction:
                raise exceptions.TransactionNotFoundError("Transaction not found")

            await self.uow.flush()

            self._publish_deleted_events(transaction)

        return api_schemas.DeleteTransactionResponse(
            transaction_id=transaction_id,
            deleted=True,
        )

    async def get_transactions_by_month_for_goal(
        self,
        user_id: UUID,
        account_id: UUID,
    ) -> list[api_schemas.TransactionsByMonthResponse]:
        """Возвращает транзакции цели, агрегированные по месяцам."""
        async with self.uow:
            rows = await self.uow.transactions.aggregate_by_month_for_account(
                user_id,
                account_id,
            )

        return [
            api_schemas.TransactionsByMonthResponse(
                amount=amount,
                period_start=period_start,
                transaction_type=enums.TransactionType(transaction_type),
                )
                for amount, period_start, transaction_type in rows
            ]

    async def apply_classification(
        self,
        user_id: UUID,
        transaction_id: UUID,
        category_id: int,
        publish_category_changed: bool = False,
    ) -> None:
        """Применяет результат классификации к транзакции."""
        async with self.uow:
            transaction = await self.uow.transactions.get_user_transaction_for_update(
                user_id,
                transaction_id,
            )
            if not transaction:
                logger.warning(
                    "Transaction %s not found for classification",
                    transaction_id,
                )
                return

            old_category_id = transaction.category_id
            transaction.category_id = category_id
            transaction.updated_at = _utc_now()

            self._queue_transaction_updated_event(
                transaction=transaction,
                old_category_id=old_category_id,
                new_category_id=category_id,
            )

            if publish_category_changed and old_category_id != category_id:
                self._queue_category_changed_event(
                    transaction=transaction,
                    old_category_id=old_category_id,
                    new_category_id=category_id,
                )

    def _queue_event(
        self,
        topic: str,
        payload: Any,
        event_type: str | None = None,
    ) -> None:
        """Добавляет событие в outbox."""
        data = (
            payload.model_dump(
                mode="json",
                by_alias=True,
                exclude_none=True,
            )
            if hasattr(payload, "model_dump")
            else payload
        )

        resolved_event_type = event_type
        if resolved_event_type is None and isinstance(data, dict):
            resolved_event_type = data.get("event_type")

        self.uow.outbox.add_event(
            topic=topic,
            payload=data,
            event_type=resolved_event_type,
        )

    def _queue_transaction_created_event(self, transaction: models.Transaction) -> None:
        """Добавляет transaction.created event."""
        payload = TransactionPayload(
            transaction_id=transaction.transaction_id,
            user_id=transaction.user_id,
            account_id=transaction.account_id,
            category_id=transaction.category_id,
            category_name_snapshot=None,
            goal_id=(
                transaction.account_id
                if self._is_goal_transaction(transaction)
                else None
            ),
            amount=_transaction_amount(transaction),
            transaction_type=_transaction_type(transaction).value,
            merchant=transaction.merchant,
            mcc=transaction.mcc,
            description=transaction.description,
            date=_transaction_occurred_at(transaction),
        )
        event = create_transaction_created_event(payload)

        self._queue_event(
            settings.KAFKA.KAFKA_TOPIC_TRANSACTION_EVENTS,
            event,
        )

    def _publish_created_events(self, transaction: models.Transaction) -> None:
        """Публикует события создания транзакции."""
        self._queue_transaction_created_event(transaction)

        if self._is_goal_transaction(transaction):
            self._queue_goal_event(transaction)
            return

        if transaction.category_id is None:
            self._queue_need_category_event(transaction)

    def _publish_imported_events(self, transaction: models.Transaction) -> None:
        """Публикует события импортированной транзакции как обычное создание."""
        self._publish_created_events(transaction)

    def _publish_category_changed_events(
        self,
        transaction: models.Transaction,
        old_category_id: int | None,
        new_category_id: int | None,
    ) -> None:
        """Публикует события изменения категории транзакции."""
        self._queue_transaction_updated_event(
            transaction=transaction,
            old_category_id=old_category_id,
            new_category_id=new_category_id,
        )

        if old_category_id != new_category_id:
            self._queue_category_changed_event(
                transaction=transaction,
                old_category_id=old_category_id,
                new_category_id=new_category_id,
            )

    def _publish_deleted_events(
        self,
        transaction: models.Transaction,
    ) -> None:
        """Публикует событие удаления транзакции."""
        payload = TransactionDeletedPayload(
            transaction_id=transaction.transaction_id,
            user_id=transaction.user_id,
            account_id=transaction.account_id,
            category_id=transaction.category_id,
            goal_id=(
                transaction.account_id
                if self._is_goal_transaction(transaction)
                else None
            ),
            amount=_transaction_amount(transaction),
            transaction_type=_transaction_type(transaction).value,
            date=_transaction_event_date(transaction),
        )
        event = create_transaction_deleted_event(payload)

        self._queue_event(
            settings.KAFKA.KAFKA_TOPIC_TRANSACTION_EVENTS,
            event,
        )

    def _queue_transaction_updated_event(
        self,
        transaction: models.Transaction,
        old_category_id: int | None,
        new_category_id: int | None,
    ) -> None:
        """Добавляет transaction.updated event."""
        payload = TransactionUpdatedPayload(
            transaction_id=transaction.transaction_id,
            user_id=transaction.user_id,
            account_id=transaction.account_id,
            category_id=transaction.category_id,
            category_name_snapshot=None,
            goal_id=(
                transaction.account_id
                if self._is_goal_transaction(transaction)
                else None
            ),
            amount=_transaction_amount(transaction),
            transaction_type=_transaction_type(transaction).value,
            merchant=transaction.merchant,
            mcc=transaction.mcc,
            description=transaction.description,
            date=_transaction_occurred_at(transaction),
            old_category_id=old_category_id,
            new_category_id=new_category_id,
            old_amount=None,
            new_amount=_transaction_amount(transaction),
        )
        event = create_transaction_updated_event(payload)

        self._queue_event(
            settings.KAFKA.KAFKA_TOPIC_TRANSACTION_EVENTS,
            event,
        )

    def _queue_need_category_event(self, transaction: models.Transaction) -> None:
        """Добавляет transaction.need_category event."""
        payload = TransactionNeedCategoryPayload(
            transaction_id=transaction.transaction_id,
            user_id=transaction.user_id,
            account_id=transaction.account_id,
            merchant=transaction.merchant,
            mcc=transaction.mcc,
            description=transaction.description,
            amount=_transaction_amount(transaction),
            transaction_type=_transaction_type(transaction).value,
            date=_transaction_occurred_at(transaction),
        )
        event = create_transaction_need_category_event(payload)

        self._queue_event(
            settings.KAFKA.KAFKA_TOPIC_TRANSACTION_EVENTS,
            event,
        )

    def _queue_category_changed_event(
        self,
        transaction: models.Transaction,
        old_category_id: int | None,
        new_category_id: int | None,
    ) -> None:
        """Добавляет transaction.category.changed event для уведомлений."""
        payload = TransactionCategoryChangedPayload(
            transaction_id=transaction.transaction_id,
            user_id=transaction.user_id,
            old_category_id=old_category_id,
            new_category_id=new_category_id,
        )
        event = create_transaction_category_changed_event(payload)

        self._queue_event(
            settings.KAFKA.KAFKA_TOPIC_TRANSACTION_EVENTS,
            event,
        )

    def _queue_goal_event(self, transaction: models.Transaction) -> None:
        """Добавляет transaction.goal_applied event."""
        if not transaction.account_id:
            return

        payload = TransactionGoalAppliedPayload(
            transaction_id=transaction.transaction_id,
            goal_id=transaction.account_id,
            user_id=transaction.user_id,
            amount=_transaction_amount(transaction),
            transaction_type=_transaction_type(transaction).value,
            date=_transaction_occurred_at(transaction),
        )
        event = create_transaction_goal_applied_event(payload)

        self._queue_event(
            settings.KAFKA.KAFKA_TOPIC_TRANSACTION_EVENTS,
            event,
        )

    @staticmethod
    def _is_goal_transaction(transaction: models.Transaction) -> bool:
        """Проверяет, что транзакция относится к цели."""
        return (
            transaction.category_id == settings.APP.GOAL_CATEGORY_ID
            and _has_goal_account(transaction.account_id)
        )

    @staticmethod
    def _build_manual_transaction(
        user_id: UUID,
        request: api_schemas.CreateManualTransactionRequest,
        now: datetime,
    ) -> models.Transaction:
        """Создает ORM-модель ручной транзакции."""
        transaction_type = request.transaction_type
        category_id = request.category_id
        description = request.description or ""

        if _has_goal_account(request.account_id):
            category_id = settings.APP.GOAL_CATEGORY_ID
            description = _goal_transaction_description(transaction_type)

        return models.Transaction(
            user_id=user_id,
            transaction_id=uuid4(),
            account_id=request.account_id,
            category_id=category_id,
            date=_ensure_aware(request.date or now),
            amount=request.amount,
            transaction_type=transaction_type.value,
            status=request.status.value,
            merchant=request.merchant or "",
            mcc=request.mcc,
            description=description,
            created_at=now,
            imported_at=now,
            updated_at=now,
        )

    def _prepare_import_transactions(
        self,
        items: list[api_schemas.ImportTransactionItemRequest],
        request_user_id: UUID | None,
    ) -> list[models.Transaction]:
        """Подготавливает импортируемые транзакции и убирает дубли внутри request."""
        prepared_transactions: list[models.Transaction] = []
        seen_transaction_ids: set[UUID] = set()

        for item in items:
            resolved_user_id = self._resolve_import_user_id(
                item=item,
                request_user_id=request_user_id,
            )
            if resolved_user_id is None:
                continue

            transaction = self._build_import_transaction(
                item=item,
                user_id=resolved_user_id,
            )

            if transaction.transaction_id in seen_transaction_ids:
                continue

            seen_transaction_ids.add(transaction.transaction_id)
            prepared_transactions.append(transaction)

        return prepared_transactions

    @staticmethod
    def _resolve_import_user_id(
        item: api_schemas.ImportTransactionItemRequest,
        request_user_id: UUID | None,
    ) -> UUID | None:
        """Определяет user_id для импортируемой транзакции."""
        if request_user_id:
            if (
                item.user_id
                and item.user_id != EMPTY_UUID
                and item.user_id != request_user_id
            ):
                raise exceptions.TransactionAccessDeniedError(
                    "Imported transaction user_id does not match current user",
                )

            return request_user_id

        if not item.user_id or item.user_id == EMPTY_UUID:
            return None

        return item.user_id

    @staticmethod
    def _build_import_transaction(
        item: api_schemas.ImportTransactionItemRequest,
        user_id: UUID,
    ) -> models.Transaction:
        """Создает ORM-модель импортируемой транзакции."""
        now = _utc_now()
        transaction_type = item.transaction_type
        category_id = item.category_id
        description = item.description or ""

        if _has_goal_account(item.account_id):
            category_id = settings.APP.GOAL_CATEGORY_ID
            description = _goal_transaction_description(transaction_type)

        return models.Transaction(
            user_id=user_id,
            transaction_id=uuid4(),
            account_id=item.account_id,
            category_id=category_id,
            date=_ensure_aware(item.date),
            amount=item.amount,
            transaction_type=transaction_type.value,
            status=(item.status or enums.TransactionStatus.PENDING).value,
            merchant=item.merchant or "",
            mcc=item.mcc,
            description=description,
            created_at=now,
            imported_at=now,
            updated_at=now,
        )
