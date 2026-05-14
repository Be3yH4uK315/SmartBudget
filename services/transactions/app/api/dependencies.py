from datetime import date, datetime, time, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import Depends, HTTPException, Query, Request, status

from app.domain.enums import TransactionType
from app.infrastructure.db.uow import UnitOfWork
from app.services.service import TransactionService


async def get_uow(request: Request) -> UnitOfWork:
    """Создает UnitOfWork с фабрикой сессий из app.state."""
    db_session_maker = getattr(request.app.state, "db_session_maker", None)
    if db_session_maker is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database session factory not available",
        )

    return UnitOfWork(db_session_maker)


def get_transaction_service(
    uow: UnitOfWork = Depends(get_uow),
) -> TransactionService:
    """Создает сервис транзакций."""
    return TransactionService(uow)


async def get_current_user_id(request: Request) -> UUID:
    """Извлекает user_id из X-User-Id, который устанавливает API Gateway."""
    user_id = request.headers.get("X-User-Id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID header missing",
        )

    try:
        return UUID(user_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid User ID format",
        ) from exc


async def get_optional_current_user_id(request: Request) -> UUID | None:
    """Извлекает optional user_id из X-User-Id."""
    user_id = request.headers.get("X-User-Id")
    if not user_id:
        return None

    try:
        return UUID(user_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid User ID format",
        ) from exc


def _parse_category_ids(raw_value: str | None) -> list[int] | None:
    """Парсит category ids из одного числа или comma-separated строки."""
    if not raw_value:
        return None

    try:
        category_ids = [
            int(part.strip())
            for part in raw_value.split(",")
            if part.strip()
        ]
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="categoryId/categoryIds must be integer or comma-separated integers",
        ) from exc

    if any(category_id <= 0 for category_id in category_ids):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="categoryId/categoryIds values must be positive integers",
        )

    return category_ids or None


class TransactionFilters:
    """Query-фильтры списка транзакций."""

    def __init__(
        self,
        limit: int = Query(50, ge=1, le=1000),
        offset: int = Query(0, ge=0),
        category_id: str | None = Query(None, alias="categoryId"),
        category_ids: str | None = Query(None, alias="categoryIds"),
        occurred_from: date | None = Query(None, alias="occurredFrom"),
        occurred_to: date | None = Query(None, alias="occurredTo"),
        transaction_type: TransactionType | None = Query(None, alias="transactionType"),
        amount_from: Decimal | None = Query(None, ge=0, alias="amountFrom"),
        amount_to: Decimal | None = Query(None, ge=0, alias="amountTo"),
    ) -> None:
        if category_id and category_ids:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Use either categoryId or categoryIds, not both",
            )

        if occurred_from and occurred_to and occurred_from > occurred_to:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="occurredFrom must be less than or equal to occurredTo",
            )

        if amount_from is not None and amount_to is not None and amount_from > amount_to:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="amountFrom must be less than or equal to amountTo",
            )

        self.limit = limit
        self.offset = offset
        self.category_ids = _parse_category_ids(category_ids or category_id)
        self.occurred_from = (
            datetime.combine(occurred_from, time.min, tzinfo=timezone.utc)
            if occurred_from
            else None
        )
        self.occurred_to = (
            datetime.combine(occurred_to, time.max, tzinfo=timezone.utc)
            if occurred_to
            else None
        )
        self.transaction_type = transaction_type
        self.amount_from = amount_from
        self.amount_to = amount_to
