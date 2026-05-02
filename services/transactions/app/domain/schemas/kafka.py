from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from app.domain.enums import TransactionType


def to_camel(string: str) -> str:
    parts = string.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])


class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        json_encoders={Decimal: float},
    )


class TransactionClassifiedMessage(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    transaction_id: UUID = Field(
        validation_alias=AliasChoices("transaction_id", "transactionId", "TransactionId"),
    )
    category_id: int | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "category_id",
            "categoryId",
            "CategoryId",
            "new_category_id",
            "newCategoryId",
            "NewCategoryId",
        ),
    )


class TransactionNewMessage(CamelModel):
    user_id: UUID
    category_id: int | None
    value: Decimal
    type: TransactionType


class TransactionNewGoalMessage(CamelModel):
    transaction_id: UUID
    goal_id: UUID
    account_id: UUID | None = None
    user_id: UUID
    value: Decimal
    type: TransactionType


class TransactionImportedMessage(CamelModel):
    event_type: str
    user_id: UUID
    details: dict[str, Any]


class TransactionNeedCategoryMessage(CamelModel):
    transaction_id: UUID
    user_id: UUID | None = None
    account_id: UUID | None = None
    merchant: str
    mcc: int | None = None
    description: str | None = None
    value: Decimal | None = None


class TransactionUpdatedMessage(CamelModel):
    transaction_id: UUID
    old_category_id: int | None
    new_category_id: int | None
    value: Decimal
    type: TransactionType


class TransactionDeletedMessage(CamelModel):
    transaction_id: UUID
    user_id: UUID


class BudgetEventMessage(CamelModel):
    event_type: str
    user_id: UUID
    details: dict[str, Any]


class NotificationEvent(CamelModel):
    event_id: UUID
    event_name: str
    user_id: UUID
    payload: dict[str, Any]
    timestamp: datetime
