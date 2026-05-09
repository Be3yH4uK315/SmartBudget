from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import TransactionStatus, TransactionType


def to_camel(string: str) -> str:
    parts = string.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])


class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        json_encoders={Decimal: float},
    )


class CreateManualTransactionRequest(CamelModel):
    account_id: UUID | None = None
    amount: Decimal = Field(..., ge=0)
    transaction_type: TransactionType
    occurred_at: datetime | None = None
    category_id: int | None = None
    description: str | None = ""
    merchant: str | None = None


class PatchTransactionCategoryRequest(CamelModel):
    category_id: int | None = None


class TransactionResponse(CamelModel):
    transaction_id: UUID
    amount: Decimal
    category_id: int | None = None
    description: str | None = None
    merchant: str
    mcc: int | None = None
    status: TransactionStatus
    occurred_at: datetime
    transaction_type: TransactionType


class TransactionDetailResponse(CamelModel):
    user_id: UUID
    transaction_id: UUID
    account_id: UUID | None = None
    category_id: int | None = None
    occurred_at: datetime
    amount: Decimal
    transaction_type: TransactionType
    status: TransactionStatus
    merchant: str
    mcc: int | None = None
    description: str | None = None
    created_at: datetime
    imported_at: datetime
    updated_at: datetime


class ImportTransactionItem(CamelModel):
    model_config = ConfigDict(populate_by_name=True)

    user_id: UUID | None = None
    transaction_id: UUID
    account_id: UUID | None = None
    occurred_at: datetime
    amount: Decimal = Field(..., ge=0)
    transaction_type: TransactionType
    status: TransactionStatus | None = None
    merchant: str | None = ""
    mcc: int | None = None
    description: str | None = ""
    category_id: int | None = None


class TransactionsByMonth(CamelModel):
    amount: Decimal
    period_start: datetime
    transaction_type: TransactionType
