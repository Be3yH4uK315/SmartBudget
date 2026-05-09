import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

from app.core import exceptions
from app.core.config import settings
from app.domain import enums
from app.domain.schemas import api as api_schemas
from app.domain.schemas import kafka as kafka_schemas
from app.infrastructure.db import models
from app.infrastructure.db.uow import UnitOfWork

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
    return _ensure_aware(transaction.occurred_at)


def _transaction_event_date(transaction: models.Transaction) -> datetime:
    """Возвращает дату транзакции для событий."""
    return _transaction_occurred_at(transaction)


def _notification_event_id(event_name: str, key: str) -> UUID:
    """Создает детерминированный notification event id."""
    return uuid5(NAMESPACE_URL, f"smartbudget:notifications:{event_name}:{key}")


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
        occurred_at=_transaction_occurred_at(transaction),
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
        occurred_at=_transaction_occurred_at(transaction),
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


def _model_to_details_dict(transaction: models.Transaction) -> dict[str, Any]:
    """Преобразует транзакцию в details dict для Kafka-событий."""
    return _model_to_detail(transaction).model_dump(
        mode="json",
        by_alias=False,
    )


class TransactionService:
    """Сервис управления транзакциями пользователя."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def list_transactions(
        self,
        user_id: UUID,
        limit: int,
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
                limit=limit,
                offset=offset,
                category_ids=category_ids,
                occurred_from=occurred_from,
                occurred_to=occurred_to,
                transaction_type=transaction_type.value if transaction_type else None,
                amount_from=amount_from,
                amount_to=amount_to,
            )

        return [
            _model_to_api(transaction)
            for transaction in transactions
        ]

    async def search_transactions(
        self,
        user_id: UUID,
        query: str,
        limit: int,
    ) -> list[api_schemas.TransactionResponse]:
        """Ищет транзакции пользователя по merchant или description."""
        normalized_query = query.strip()
        if not normalized_query:
            return []

        async with self.uow:
            transactions = await self.uow.transactions.search_user_transactions(
                user_id=user_id,
                query_text=normalized_query,
                limit=limit,
            )

        return [
            _model_to_api(transaction)
            for transaction in transactions
        ]

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
    ) -> str:
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

        return str(transaction.transaction_id)

    async def import_mock_transactions(
        self,
        items: list[api_schemas.ImportTransactionItem],
        request_user_id: UUID | None = None,
    ) -> int:
        """Импортирует mock-транзакции."""
        prepared_transactions = self._prepare_import_transactions(
            items=items,
            request_user_id=request_user_id,
        )
        if not prepared_transactions:
            return 0

        imported_count = 0

        async with self.uow:
            existing_ids = await self.uow.transactions.get_existing_transaction_ids(
                [
                    transaction.transaction_id
                    for transaction in prepared_transactions
                ],
            )

            for transaction in prepared_transactions:
                if transaction.transaction_id in existing_ids:
                    continue

                self.uow.transactions.create(transaction)
                self._publish_imported_events(transaction)
                imported_count += 1

        return imported_count

    async def patch_category(
        self,
        user_id: UUID,
        transaction_id: UUID,
        category_id: int | None,
    ) -> str:
        """Изменяет категорию транзакции пользователя."""
        async with self.uow:
            transaction = await self.uow.transactions.get_user_transaction_for_update(
                user_id,
                transaction_id,
            )
            if not transaction:
                raise exceptions.TransactionNotFoundError("Transaction not found")

            old_category_id = transaction.category_id
            transaction.category_id = category_id
            transaction.updated_at = _utc_now()

            await self.uow.flush()

            self._publish_category_changed_events(
                transaction=transaction,
                old_category_id=old_category_id,
                new_category_id=category_id,
            )

        return "OK"

    async def delete_transaction(self, transaction_id: UUID) -> None:
        """Удаляет транзакцию без проверки владельца."""
        async with self.uow:
            transaction = await self.uow.transactions.delete_by_transaction_id(
                transaction_id,
            )
            if not transaction:
                return

            await self.uow.flush()

            self._publish_deleted_events(
                user_id=transaction.user_id,
                transaction_id=transaction_id,
                transaction_date=_transaction_event_date(transaction),
            )

    async def delete_user_transaction(
        self,
        user_id: UUID,
        transaction_id: UUID,
    ) -> None:
        """Удаляет транзакцию пользователя."""
        async with self.uow:
            transaction = await self.uow.transactions.delete_user_transaction(
                user_id,
                transaction_id,
            )
            if not transaction:
                return

            await self.uow.flush()

            self._publish_deleted_events(
                user_id=transaction.user_id,
                transaction_id=transaction_id,
                transaction_date=_transaction_event_date(transaction),
            )

    async def get_transactions_by_month_for_goal(
        self,
        user_id: UUID,
        account_id: UUID,
    ) -> list[api_schemas.TransactionsByMonth]:
        """Возвращает транзакции цели, агрегированные по месяцам."""
        async with self.uow:
            rows = await self.uow.transactions.aggregate_by_month_for_account(
                user_id,
                account_id,
            )

        return [
            api_schemas.TransactionsByMonth(
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

        self.uow.outbox.add_event(
            topic=topic,
            payload=data,
            event_type=event_type,
        )

    def _publish_created_events(self, transaction: models.Transaction) -> None:
        """Публикует события создания транзакции."""
        self._queue_transaction_new_event(transaction)
        self._queue_budget_transaction_event("transaction.new", transaction)

        if self._is_goal_transaction(transaction):
            self._queue_goal_event(transaction)

    def _publish_imported_events(self, transaction: models.Transaction) -> None:
        """Публикует события импорта транзакции."""
        self._queue_event(
            settings.KAFKA.KAFKA_TOPIC_TRANSACTION_IMPORTED,
            kafka_schemas.TransactionImportedMessage(
                event_type="transaction.imported",
                user_id=transaction.user_id,
                details=_model_to_details_dict(transaction),
            ),
            "transaction.imported",
        )

        if self._is_goal_transaction(transaction):
            self._queue_transaction_new_event(transaction)
            self._queue_goal_event(transaction)
            return

        self._queue_need_category_event(transaction)

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
        self._queue_budget_category_changed_event(
            transaction=transaction,
            old_category_id=old_category_id,
            new_category_id=new_category_id,
        )

        if old_category_id != new_category_id:
            self._queue_category_changed_notification(
                transaction=transaction,
                old_category_id=old_category_id,
                new_category_id=new_category_id,
            )

    def _publish_deleted_events(
        self,
        user_id: UUID,
        transaction_id: UUID,
        transaction_date: datetime,
    ) -> None:
        """Публикует события удаления транзакции."""
        self._queue_event(
            settings.KAFKA.KAFKA_TOPIC_TRANSACTION_DELETED,
            kafka_schemas.TransactionDeletedMessage(
                transaction_id=transaction_id,
                user_id=user_id,
                occurred_at=transaction_date,
            ),
            "transaction.deleted",
        )
        self._queue_event(
            settings.KAFKA.KAFKA_TOPIC_BUDGET_EVENTS,
            kafka_schemas.BudgetEventMessage(
                event_type="transaction.deleted",
                user_id=user_id,
                details={
                    "transaction_id": str(transaction_id),
                },
            ),
            "transaction.deleted",
        )

    def _queue_transaction_new_event(self, transaction: models.Transaction) -> None:
        """Добавляет transaction.new event."""
        self._queue_event(
            settings.KAFKA.KAFKA_TOPIC_TRANSACTION_NEW,
            kafka_schemas.TransactionNewMessage(
                transaction_id=transaction.transaction_id,
                user_id=transaction.user_id,
                category_id=transaction.category_id,
                amount=_transaction_amount(transaction),
                transaction_type=_transaction_type(transaction),
                occurred_at=_transaction_occurred_at(transaction),
            ),
            "transaction.new",
        )

    def _queue_transaction_updated_event(
        self,
        transaction: models.Transaction,
        old_category_id: int | None,
        new_category_id: int | None,
    ) -> None:
        """Добавляет transaction.updated event."""
        self._queue_event(
            settings.KAFKA.KAFKA_TOPIC_TRANSACTION_UPDATED,
            kafka_schemas.TransactionUpdatedMessage(
                transaction_id=transaction.transaction_id,
                user_id=transaction.user_id,
                old_category_id=old_category_id,
                new_category_id=new_category_id,
                amount=_transaction_amount(transaction),
                transaction_type=_transaction_type(transaction),
                occurred_at=_transaction_occurred_at(transaction),
            ),
            "transaction.updated",
        )

    def _queue_budget_transaction_event(
        self,
        event_type: str,
        transaction: models.Transaction,
    ) -> None:
        """Добавляет budget event с полной транзакцией в details."""
        self._queue_event(
            settings.KAFKA.KAFKA_TOPIC_BUDGET_EVENTS,
            kafka_schemas.BudgetEventMessage(
                event_type=event_type,
                user_id=transaction.user_id,
                details=_model_to_details_dict(transaction),
            ),
            event_type,
        )

    def _queue_budget_category_changed_event(
        self,
        transaction: models.Transaction,
        old_category_id: int | None,
        new_category_id: int | None,
    ) -> None:
        """Добавляет budget event изменения категории."""
        self._queue_event(
            settings.KAFKA.KAFKA_TOPIC_BUDGET_EVENTS,
            kafka_schemas.BudgetEventMessage(
                event_type="transaction.updated",
                user_id=transaction.user_id,
                details={
                    "transaction_id": str(transaction.transaction_id),
                    "old_category_id": old_category_id,
                    "new_category_id": new_category_id,
                },
            ),
            "transaction.updated",
        )

    def _queue_need_category_event(self, transaction: models.Transaction) -> None:
        """Добавляет transaction.need_category event."""
        self._queue_event(
            settings.KAFKA.KAFKA_TOPIC_TRANSACTION_NEED_CATEGORY,
            kafka_schemas.TransactionNeedCategoryMessage(
                transaction_id=transaction.transaction_id,
                user_id=transaction.user_id,
                account_id=transaction.account_id,
                merchant=transaction.merchant,
                mcc=transaction.mcc,
                description=transaction.description,
                amount=_transaction_amount(transaction),
            ),
            "transaction.need_category",
        )

    def _queue_category_changed_notification(
        self,
        transaction: models.Transaction,
        old_category_id: int | None,
        new_category_id: int | None,
    ) -> None:
        """Добавляет notification event изменения категории."""
        self._queue_event(
            settings.KAFKA.KAFKA_TOPIC_NOTIFICATION_EVENTS,
            kafka_schemas.NotificationEvent(
                event_id=_notification_event_id(
                    "transaction.category.changed",
                    (
                        f"{transaction.transaction_id}:"
                        f"{old_category_id}:"
                        f"{new_category_id}"
                    ),
                ),
                event_type="transaction.category.changed",
                user_id=transaction.user_id,
                payload={
                    "transaction_id": str(transaction.transaction_id),
                    "old_category_id": old_category_id,
                    "new_category_id": new_category_id,
                },
                timestamp=_utc_now(),
            ),
            "transaction.category.changed",
        )

    def _queue_goal_event(self, transaction: models.Transaction) -> None:
        """Добавляет transaction.goal event."""
        if not transaction.account_id:
            return

        self._queue_event(
            settings.KAFKA.KAFKA_TOPIC_TRANSACTION_GOAL,
            kafka_schemas.TransactionNewGoalMessage(
                transaction_id=transaction.transaction_id,
                goal_id=transaction.account_id,
                user_id=transaction.user_id,
                amount=_transaction_amount(transaction),
                transaction_type=_transaction_type(transaction),
                occurred_at=_transaction_occurred_at(transaction),
            ),
            "transaction.goal",
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
            occurred_at=_ensure_aware(request.occurred_at or now),
            amount=request.amount,
            transaction_type=transaction_type.value,
            status=enums.TransactionStatus.CONFIRMED.value,
            merchant=request.merchant or "",
            description=description,
            created_at=now,
            imported_at=now,
            updated_at=now,
        )

    def _prepare_import_transactions(
        self,
        items: list[api_schemas.ImportTransactionItem],
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
        item: api_schemas.ImportTransactionItem,
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
        item: api_schemas.ImportTransactionItem,
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
            transaction_id=item.transaction_id,
            account_id=item.account_id,
            category_id=category_id,
            occurred_at=_ensure_aware(item.occurred_at),
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
