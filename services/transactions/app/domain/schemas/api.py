from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

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
    value: Decimal
    category_id: int | None = None
    description: str | None = ""
    name: str = ""


class PatchTransactionCategoryRequest(CamelModel):
    category_id: int | None = None


class TransactionResponse(CamelModel):
    transaction_id: UUID
    value: Decimal
    category_id: int | None = None
    description: str | None = None
    name: str
    mcc: int | None = None
    status: TransactionStatus
    date: datetime
    type: TransactionType


class TransactionDetailResponse(CamelModel):
    id: UUID
    user_id: UUID
    transaction_id: UUID
    account_id: UUID | None = None
    category_id: int | None = None
    date: datetime | None = None
    value: Decimal
    type: TransactionType
    status: TransactionStatus
    merchant: str
    mcc: int | None = None
    description: str | None = None
    created_at: datetime
    imported_at: datetime
    updated_at: datetime


class ImportTransactionItem(CamelModel):
    model_config = ConfigDict(populate_by_name=True)

    id: UUID | None = Field(default=None, validation_alias=AliasChoices("id", "Id"))
    user_id: UUID | None = Field(default=None, validation_alias=AliasChoices("user_id", "userId", "UserId"))
    transaction_id: UUID | None = Field(
        default=None,
        validation_alias=AliasChoices("transaction_id", "transactionId", "TransactionId"),
    )
    account_id: UUID | None = Field(
        default=None,
        validation_alias=AliasChoices("account_id", "accountId", "AccountId"),
    )
    date: datetime | None = Field(default=None, validation_alias=AliasChoices("date", "Date"))
    value: Decimal | None = Field(default=None, validation_alias=AliasChoices("value", "Value"))
    type: TransactionType | None = Field(default=None, validation_alias=AliasChoices("type", "Type"))
    status: TransactionStatus | None = Field(default=None, validation_alias=AliasChoices("status", "Status"))
    merchant: str | None = Field(default="", validation_alias=AliasChoices("merchant", "Merchant"))
    mcc: int | None = Field(default=None, validation_alias=AliasChoices("mcc", "Mcc", "MCC"))
    description: str | None = Field(default="", validation_alias=AliasChoices("description", "Description"))
    category_id: int | None = Field(
        default=None,
        validation_alias=AliasChoices("category_id", "categoryId", "CategoryId"),
    )

    @field_validator("type", mode="before")
    @classmethod
    def parse_type(cls, value: Any) -> Any:
        if isinstance(value, int):
            return TransactionType.INCOME if value == 0 else TransactionType.EXPENSE
        if isinstance(value, str):
            return value.lower()
        return value

    @field_validator("status", mode="before")
    @classmethod
    def parse_status(cls, value: Any) -> Any:
        if isinstance(value, int):
            return {
                0: TransactionStatus.REJECTED,
                1: TransactionStatus.CONFIRMED,
                2: TransactionStatus.PENDING,
            }.get(value)
        if isinstance(value, str):
            return value.lower()
        return value


class TransactionsByMonth(CamelModel):
    value: Decimal
    date: datetime
    type: TransactionType
