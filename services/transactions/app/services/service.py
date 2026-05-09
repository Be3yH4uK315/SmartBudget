import logging
from datetime import datetime, timezone
from decimal import Decimal
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
    return datetime.now(timezone.utc)


def _ensure_aware(value: datetime | None) -> datetime:
    if value is None:
        return _utc_now()
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _transaction_amount(transaction: models.Transaction) -> Decimal:
    return transaction.amount


def _transaction_type(transaction: models.Transaction) -> enums.TransactionType:
    return enums.TransactionType(transaction.transaction_type)


def _transaction_status(transaction: models.Transaction) -> enums.TransactionStatus:
    return enums.TransactionStatus(transaction.status)


def _transaction_occurred_at(transaction: models.Transaction) -> datetime:
    return _ensure_aware(transaction.occurred_at)


def _model_to_api(transaction: models.Transaction) -> api_schemas.TransactionResponse:
    amount = _transaction_amount(transaction)
    transaction_type = _transaction_type(transaction)
    occurred_at = _transaction_occurred_at(transaction)
    return api_schemas.TransactionResponse(
        transaction_id=transaction.transaction_id,
        amount=amount,
        category_id=transaction.category_id,
        description=transaction.description,
        merchant=transaction.merchant,
        mcc=transaction.mcc,
        status=_transaction_status(transaction),
        occurred_at=occurred_at,
        transaction_type=transaction_type,
    )


def _model_to_detail(
    transaction: models.Transaction,
) -> api_schemas.TransactionDetailResponse:
    amount = _transaction_amount(transaction)
    transaction_type = _transaction_type(transaction)
    occurred_at = _transaction_occurred_at(transaction)
    return api_schemas.TransactionDetailResponse(
        user_id=transaction.user_id,
        transaction_id=transaction.transaction_id,
        account_id=transaction.account_id,
        category_id=transaction.category_id,
        occurred_at=occurred_at,
        amount=amount,
        transaction_type=transaction_type,
        status=_transaction_status(transaction),
        merchant=transaction.merchant,
        mcc=transaction.mcc,
        description=transaction.description,
        created_at=transaction.created_at,
        imported_at=transaction.imported_at,
        updated_at=transaction.updated_at,
    )


def _model_to_details_dict(transaction: models.Transaction) -> dict:
    return _model_to_detail(transaction).model_dump(mode="json", by_alias=False)


def _transaction_event_date(transaction: models.Transaction) -> datetime:
    return _transaction_occurred_at(transaction)


def _notification_event_id(event_name: str, key: str) -> UUID:
    return uuid5(NAMESPACE_URL, f"smartbudget:notifications:{event_name}:{key}")


def _has_goal_account(account_id: UUID | None) -> bool:
    return account_id is not None and account_id != EMPTY_UUID


class TransactionService:
    """Сервис для управления транзакциями пользователя."""

    def __init__(self, uow: UnitOfWork):
        """Инициализирует сервис с юнитом работы.

        Args:
            uow: Unit of Work для доступа к репозиториям данных.
        """
        self.uow = uow

    def _queue_event(self, topic: str, payload, event_type: str | None = None) -> None:
        """Добавляет событие в очередь исходящих событий."""
        if hasattr(payload, "model_dump"):
            data = payload.model_dump(mode="json", by_alias=True, exclude_none=True)
        else:
            data = payload

        self.uow.outbox.add_event(topic, data, event_type)

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
        """Получает список транзакций пользователя с фильтрацией и пагинацией."""
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

        return [_model_to_api(transaction) for transaction in transactions]

    async def search_transactions(
        self,
        user_id: UUID,
        query: str,
        limit: int,
    ) -> list[api_schemas.TransactionResponse]:
        """Поиск транзакций по текстовому запросу."""
        normalized_query = query.strip()
        if not normalized_query:
            return []

        async with self.uow:
            transactions = await self.uow.transactions.search_user_transactions(
                user_id,
                normalized_query,
                limit,
            )

        return [_model_to_api(transaction) for transaction in transactions]

    async def get_transaction(
        self,
        user_id: UUID,
        transaction_id: UUID,
    ) -> api_schemas.TransactionDetailResponse:
        """Получает детальную информацию о транзакции."""
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
        """Создает новую ручную транзакцию (не из банка)."""
        now = _utc_now()
        transaction_type = request.transaction_type
        amount = request.amount
        occurred_at = _ensure_aware(request.occurred_at or now)
        merchant = request.merchant
        category_id = request.category_id
        description = request.description or ""
        if _has_goal_account(request.account_id):
            category_id = settings.APP.GOAL_CATEGORY_ID
            description = (
                "Пополнение цели"
                if transaction_type == enums.TransactionType.INCOME
                else "Списание с цели"
            )
        transaction = models.Transaction(
            user_id=user_id,
            transaction_id=uuid4(),
            account_id=request.account_id,
            category_id=category_id,
            occurred_at=occurred_at,
            amount=amount,
            transaction_type=transaction_type.value,
            status=enums.TransactionStatus.CONFIRMED.value,
            merchant=merchant or "",
            description=description,
            created_at=now,
            imported_at=now,
            updated_at=now,
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
        """Импортирует пакет транзакций (обычно из интеграции с банком)."""
        prepared_transactions: list[models.Transaction] = []
        seen_transaction_ids: set[UUID] = set()
        count = 0

        for item in items:
            if request_user_id:
                if (
                    item.user_id
                    and item.user_id != EMPTY_UUID
                    and item.user_id != request_user_id
                ):
                    raise exceptions.TransactionAccessDeniedError(
                        "Imported transaction user_id does not match current user",
                    )
                item.user_id = request_user_id

            if not item.user_id or item.user_id == EMPTY_UUID:
                continue

            now = _utc_now()
            transaction_type = item.transaction_type
            status = item.status or enums.TransactionStatus.PENDING
            account_id = item.account_id
            category_id = item.category_id
            description = item.description or ""
            occurred_at = _ensure_aware(item.occurred_at)
            amount = item.amount

            if _has_goal_account(account_id):
                category_id = settings.APP.GOAL_CATEGORY_ID
                description = (
                    "Пополнение цели"
                    if transaction_type == enums.TransactionType.INCOME
                    else "Списание с цели"
                )

            transaction = models.Transaction(
                user_id=item.user_id,
                transaction_id=item.transaction_id,
                account_id=account_id,
                category_id=category_id,
                occurred_at=occurred_at,
                amount=amount,
                transaction_type=transaction_type.value,
                status=status.value,
                merchant=item.merchant or "",
                mcc=item.mcc,
                description=description,
                created_at=now,
                imported_at=now,
                updated_at=now,
            )

            if transaction.transaction_id in seen_transaction_ids:
                continue

            seen_transaction_ids.add(transaction.transaction_id)
            prepared_transactions.append(transaction)

        if not prepared_transactions:
            return 0

        async with self.uow:
            existing_ids = await self.uow.transactions.get_existing_transaction_ids(
                [transaction.transaction_id for transaction in prepared_transactions]
            )

            for transaction in prepared_transactions:
                if transaction.transaction_id in existing_ids:
                    continue

                self.uow.transactions.create(transaction)
                self._publish_imported_events(transaction)

                count += 1

        return count

    async def patch_category(
        self,
        user_id: UUID,
        transaction_id: UUID,
        category_id: int | None,
    ) -> str:
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

            amount = _transaction_amount(transaction)
            transaction_type = _transaction_type(transaction)
            occurred_at = _transaction_occurred_at(transaction)
            user_id = transaction.user_id

            self._queue_event(
                settings.KAFKA.KAFKA_TOPIC_TRANSACTION_UPDATED,
                kafka_schemas.TransactionUpdatedMessage(
                    transaction_id=transaction_id,
                    user_id=user_id,
                    old_category_id=old_category_id,
                    new_category_id=category_id,
                    amount=amount,
                    transaction_type=transaction_type,
                    occurred_at=occurred_at,
                ),
                "transaction.updated",
            )
            self._queue_event(
                settings.KAFKA.KAFKA_TOPIC_BUDGET_EVENTS,
                kafka_schemas.BudgetEventMessage(
                    event_type="transaction.updated",
                    user_id=user_id,
                    details={
                        "transaction_id": str(transaction_id),
                        "old_category_id": old_category_id,
                        "new_category_id": category_id,
                    },
                ),
                "transaction.updated",
            )
            if old_category_id != category_id:
                self._queue_event(
                    settings.KAFKA.KAFKA_TOPIC_NOTIFICATION_EVENTS,
                    kafka_schemas.NotificationEvent(
                        event_id=_notification_event_id(
                            "transaction.category.changed",
                            f"{transaction_id}:{old_category_id}:{category_id}",
                        ),
                        event_type="transaction.category.changed",
                        user_id=user_id,
                        payload={
                            "transaction_id": str(transaction_id),
                            "old_category_id": old_category_id,
                            "new_category_id": category_id,
                        },
                        timestamp=_utc_now(),
                    ),
                    "transaction.category.changed",
                )
        return "OK"

    async def delete_transaction(self, transaction_id: UUID) -> None:
        async with self.uow:
            transaction = await self.uow.transactions.delete_by_transaction_id(
                transaction_id
            )
            if not transaction:
                return
            await self.uow.flush()
            user_id = transaction.user_id

            self._publish_deleted_events(
                user_id,
                transaction_id,
                _transaction_event_date(transaction),
            )

    async def delete_user_transaction(
        self,
        user_id: UUID,
        transaction_id: UUID,
    ) -> None:
        async with self.uow:
            transaction = await self.uow.transactions.delete_user_transaction(
                user_id,
                transaction_id,
            )
            if not transaction:
                return
            await self.uow.flush()
            event_user_id = transaction.user_id

            self._publish_deleted_events(
                event_user_id,
                transaction_id,
                _transaction_event_date(transaction),
            )

    async def get_transactions_by_month_for_goal(
        self,
        user_id: UUID,
        account_id: UUID,
    ) -> list[api_schemas.TransactionsByMonth]:
        async with self.uow:
            rows = await self.uow.transactions.aggregate_by_month_for_account(
                user_id,
                account_id,
            )

        return [
            api_schemas.TransactionsByMonth(
                amount=value,
                period_start=month,
                transaction_type=enums.TransactionType(transaction_type),
            )
            for value, month, transaction_type in rows
        ]

    async def apply_classification(
        self,
        user_id: UUID,
        transaction_id: UUID,
        category_id: int,
    ) -> None:
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
            self._queue_event(
                settings.KAFKA.KAFKA_TOPIC_TRANSACTION_UPDATED,
                kafka_schemas.TransactionUpdatedMessage(
                    transaction_id=transaction.transaction_id,
                    user_id=transaction.user_id,
                    old_category_id=old_category_id,
                    new_category_id=category_id,
                    amount=_transaction_amount(transaction),
                    transaction_type=_transaction_type(transaction),
                    occurred_at=_transaction_occurred_at(transaction),
                ),
                "transaction.updated",
            )

    def _publish_created_events(self, transaction: models.Transaction) -> None:
        amount = _transaction_amount(transaction)
        transaction_type = _transaction_type(transaction)
        occurred_at = _transaction_occurred_at(transaction)
        self._queue_event(
            settings.KAFKA.KAFKA_TOPIC_TRANSACTION_NEW,
            kafka_schemas.TransactionNewMessage(
                transaction_id=transaction.transaction_id,
                user_id=transaction.user_id,
                category_id=transaction.category_id,
                amount=amount,
                transaction_type=transaction_type,
                occurred_at=occurred_at,
            ),
            "transaction.new",
        )
        self._queue_event(
            settings.KAFKA.KAFKA_TOPIC_BUDGET_EVENTS,
            kafka_schemas.BudgetEventMessage(
                event_type="transaction.new",
                user_id=transaction.user_id,
                details=_model_to_details_dict(transaction),
            ),
            "transaction.new",
        )

        if (
            transaction.category_id == settings.APP.GOAL_CATEGORY_ID
            and _has_goal_account(transaction.account_id)
        ):
            self._queue_goal_event(transaction)

    def _publish_imported_events(self, transaction: models.Transaction) -> None:
        self._queue_event(
            settings.KAFKA.KAFKA_TOPIC_TRANSACTION_IMPORTED,
            kafka_schemas.TransactionImportedMessage(
                event_type="transaction.imported",
                user_id=transaction.user_id,
                details=_model_to_details_dict(transaction),
            ),
            "transaction.imported",
        )

        if (
            transaction.category_id == settings.APP.GOAL_CATEGORY_ID
            and _has_goal_account(transaction.account_id)
        ):
            amount = _transaction_amount(transaction)
            transaction_type = _transaction_type(transaction)
            occurred_at = _transaction_occurred_at(transaction)
            self._queue_event(
                settings.KAFKA.KAFKA_TOPIC_TRANSACTION_NEW,
                kafka_schemas.TransactionNewMessage(
                    transaction_id=transaction.transaction_id,
                    user_id=transaction.user_id,
                    category_id=transaction.category_id,
                    amount=amount,
                    transaction_type=transaction_type,
                    occurred_at=occurred_at,
                ),
                "transaction.new",
            )
            self._queue_goal_event(transaction)
            return

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

    def _publish_deleted_events(
        self,
        user_id: UUID,
        transaction_id: UUID,
        transaction_date: datetime,
    ) -> None:
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
                details={"transaction_id": str(transaction_id)},
            ),
            "transaction.deleted",
        )

    def _queue_goal_event(self, transaction: models.Transaction) -> None:
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
