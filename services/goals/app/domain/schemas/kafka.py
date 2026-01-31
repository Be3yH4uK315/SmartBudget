from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict

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

class TransactionEvent(CamelModel):
    transaction_id: UUID = Field(..., description="ID транзакции")
    goal_id: UUID = Field(..., description="ID цели")
    user_id: UUID = Field(..., description="ID пользователя")
    value: Decimal = Field(..., gt=0, description="Сумма транзакции")
    type: TransactionType = Field(..., description="Тип транзакции")

    model_config = ConfigDict(
        from_attributes=True,
    )