from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import TransactionType


class TransactionEvent(BaseModel):
    """Событие создания или обновления транзакции цели."""

    model_config = ConfigDict(populate_by_name=True)

    transaction_id: UUID = Field(..., description="ID транзакции")
    goal_id: UUID = Field(..., description="ID цели")
    user_id: UUID = Field(..., description="ID пользователя")
    amount: Decimal = Field(..., gt=0, description="Сумма транзакции")
    transaction_type: TransactionType = Field(..., description="Тип транзакции")
    occurred_at: datetime = Field(..., description="Бизнес-время транзакции")


class TransactionDeletedEvent(BaseModel):
    """Событие удаления транзакции цели."""

    model_config = ConfigDict(populate_by_name=True)

    transaction_id: UUID = Field(..., description="ID транзакции")
    user_id: UUID = Field(..., description="ID пользователя")
    occurred_at: datetime = Field(..., description="Бизнес-время транзакции")
