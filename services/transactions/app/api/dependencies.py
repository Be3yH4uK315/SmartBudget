from datetime import date, datetime, time, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import Depends, HTTPException, Query, Request, status

from app.domain.enums import TransactionType
from app.infrastructure.db.uow import UnitOfWork
from app.services.service import TransactionService


async def get_uow(request: Request) -> UnitOfWork:
    db_session_maker = request.app.state.db_session_maker
    if not db_session_maker:
        raise HTTPException(
            status_code=500,
            detail="Database session factory not available",
        )
    return UnitOfWork(db_session_maker)


def get_transaction_service(
    uow: UnitOfWork = Depends(get_uow),
) -> TransactionService:
    return TransactionService(uow)


async def get_current_user_id(request: Request) -> UUID:
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


def _parse_category_ids(category_id: str | None) -> list[int] | None:
    if not category_id:
        return None

    try:
        result = [
            int(part.strip())
            for part in category_id.split(",")
            if part.strip()
        ]
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="categoryId must be an integer or comma-separated integers",
        ) from exc

    result = [item for item in result if item != 0]
    return result or None


class TransactionFilters:
    def __init__(
        self,
        limit: int = Query(50, ge=1, le=1000),
        offset: int = Query(0, ge=0),
        category_id: str | None = Query(None, alias="categoryId"),
        date_from: date | None = Query(None, alias="dateFrom"),
        date_to: date | None = Query(None, alias="dateTo"),
        transaction_type: TransactionType | None = Query(None, alias="type"),
        value_from: Decimal | None = Query(None, alias="valueFrom"),
        value_to: Decimal | None = Query(None, alias="valueTo"),
    ):
        self.limit = limit
        self.offset = offset
        self.category_ids = _parse_category_ids(category_id)
        self.date_from = (
            datetime.combine(date_from, time.min, tzinfo=timezone.utc)
            if date_from
            else None
        )
        self.date_to = (
            datetime.combine(date_to, time.max, tzinfo=timezone.utc)
            if date_to
            else None
        )
        self.transaction_type = transaction_type
        self.value_from = value_from
        self.value_to = value_to
