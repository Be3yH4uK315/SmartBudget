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


def _model_to_api(transaction: models.Transaction) -> api_schemas.TransactionResponse:
    return api_schemas.TransactionResponse(
        transaction_id=transaction.transaction_id,
        value=abs(transaction.value),
        category_id=transaction.category_id,
        description=transaction.description,
        name=transaction.merchant,
        mcc=transaction.mcc,
        status=enums.status_from_db(transaction.status),
        date=transaction.created_at,
        type=enums.type_from_db(transaction.type),
    )


def _model_to_detail(
    transaction: models.Transaction,
) -> api_schemas.TransactionDetailResponse:
    return api_schemas.TransactionDetailResponse(
        id=transaction.id,
        user_id=transaction.user_id,
        transaction_id=transaction.transaction_id,
        account_id=transaction.account_id,
        category_id=transaction.category_id,
        date=transaction.date,
        value=abs(transaction.value),
        type=enums.type_from_db(transaction.type),
        status=enums.status_from_db(transaction.status),
        merchant=transaction.merchant,
        mcc=transaction.mcc,
        description=transaction.description,
        created_at=transaction.created_at,
        imported_at=transaction.imported_at,
        updated_at=transaction.updated_at,
    )


def _model_to_details_dict(transaction: models.Transaction) -> dict:
    return _model_to_detail(transaction).model_dump(mode="json", by_alias=True)


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
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        transaction_type: enums.TransactionType | None = None,
        value_from: Decimal | None = None,
        value_to: Decimal | None = None,
    ) -> list[api_schemas.TransactionResponse]:
        """Получает список транзакций пользователя с фильтрацией и пагинацией."""
        async with self.uow:
            transactions = await self.uow.transactions.list_user_transactions(
                user_id=user_id,
                limit=limit,
                offset=offset,
                category_ids=category_ids,
                date_from=date_from,
                date_to=date_to,
                transaction_type=transaction_type.value if transaction_type else None,
                value_from=value_from,
                value_to=value_to,
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
        transaction_type = (
            enums.TransactionType.INCOME
            if request.value >= Decimal("0")
            else enums.TransactionType.EXPENSE
        )
        transaction = models.Transaction(
            id=uuid4(),
            user_id=user_id,
            transaction_id=uuid4(),
            account_id=request.account_id,
            category_id=request.category_id,
            value=abs(request.value),
            type=enums.type_to_db(transaction_type),
            status=enums.status_to_db(enums.TransactionStatus.CONFIRMED),
            merchant=request.name or "",
            description=request.description or "",
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
            transaction_type = item.type or enums.TransactionType.EXPENSE
            status = item.status or enums.TransactionStatus.PENDING
            account_id = item.account_id
            category_id = item.category_id
            description = item.description or ""

            if _has_goal_account(account_id):
                category_id = settings.APP.GOAL_CATEGORY_ID
                description = (
                    "Пополнение цели"
                    if transaction_type == enums.TransactionType.INCOME
                    else "Списание с цели"
                )

            transaction = models.Transaction(
                id=item.id or uuid4(),
                user_id=item.user_id,
                transaction_id=item.transaction_id or uuid4(),
                account_id=account_id,
                category_id=category_id,
                date=_ensure_aware(item.date),
                value=abs(item.value) if item.value is not None else Decimal("0"),
                type=enums.type_to_db(transaction_type),
                status=enums.status_to_db(status),
                merchant=item.merchant or "",
                mcc=item.mcc,
                description=description,
                created_at=_ensure_aware(item.date),
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

            value = abs(transaction.value)
            transaction_type = enums.type_from_db(transaction.type)
            user_id = transaction.user_id

            self._queue_event(
                settings.KAFKA.KAFKA_TOPIC_TRANSACTION_UPDATED,
                kafka_schemas.TransactionUpdatedMessage(
                    transaction_id=transaction_id,
                    old_category_id=old_category_id,
                    new_category_id=category_id,
                    value=value,
                    type=transaction_type,
                ),
                "transaction.updated",
            )
            self._queue_event(
                settings.KAFKA.KAFKA_TOPIC_BUDGET_EVENTS,
                kafka_schemas.BudgetEventMessage(
                    event_type="transaction.updated",
                    user_id=user_id,
                    details={
                        "transactionId": str(transaction_id),
                        "oldCategoryId": old_category_id,
                        "newCategoryId": category_id,
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
                        event_name="transaction.category.changed",
                        user_id=user_id,
                        payload={
                            "transactionId": str(transaction_id),
                            "oldCategory": old_category_id,
                            "newCategory": category_id,
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

            self._publish_deleted_events(user_id, transaction_id)

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

            self._publish_deleted_events(event_user_id, transaction_id)

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
                value=value,
                date=month,
                type=enums.type_from_db(transaction_type),
            )
            for value, month, transaction_type in rows
        ]

    async def apply_classification(
        self,
        transaction_id: UUID,
        category_id: int | None,
    ) -> None:
        async with self.uow:
            transaction = await self.uow.transactions.get_for_update(transaction_id)
            if not transaction:
                logger.warning(
                    "Transaction %s not found for classification",
                    transaction_id,
                )
                return

            transaction.category_id = category_id
            transaction.updated_at = _utc_now()

    def _publish_created_events(self, transaction: models.Transaction) -> None:
        transaction_type = enums.type_from_db(transaction.type)
        self._queue_event(
            settings.KAFKA.KAFKA_TOPIC_TRANSACTION_NEW,
            kafka_schemas.TransactionNewMessage(
                user_id=transaction.user_id,
                category_id=transaction.category_id,
                value=abs(transaction.value),
                type=transaction_type,
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
            transaction_type = enums.type_from_db(transaction.type)
            self._queue_event(
                settings.KAFKA.KAFKA_TOPIC_TRANSACTION_NEW,
                kafka_schemas.TransactionNewMessage(
                    user_id=transaction.user_id,
                    category_id=transaction.category_id,
                    value=abs(transaction.value),
                    type=transaction_type,
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
                value=abs(transaction.value),
            ),
            "transaction.need_category",
        )

    def _publish_deleted_events(self, user_id: UUID, transaction_id: UUID) -> None:
        self._queue_event(
            settings.KAFKA.KAFKA_TOPIC_TRANSACTION_DELETED,
            kafka_schemas.TransactionDeletedMessage(
                transaction_id=transaction_id,
                user_id=user_id,
            ),
            "transaction.deleted",
        )
        self._queue_event(
            settings.KAFKA.KAFKA_TOPIC_BUDGET_EVENTS,
            kafka_schemas.BudgetEventMessage(
                event_type="transaction.deleted",
                user_id=user_id,
                details={"transactionId": str(transaction_id)},
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
                account_id=transaction.account_id,
                user_id=transaction.user_id,
                value=abs(transaction.value),
                type=enums.type_from_db(transaction.type),
            ),
            "transaction.goal",
        )
