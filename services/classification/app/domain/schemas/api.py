from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


def to_camel(string: str) -> str:
    """Преобразует snake_case в camelCase."""
    parts = string.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])


class CamelModel(BaseModel):
    """Базовая Pydantic-модель с camelCase alias."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class FeedbackRequest(CamelModel):
    """Запрос с пользовательским feedback по классификации."""

    transaction_id: UUID = Field(..., description="ID транзакции")
    correct_category_id: int = Field(
        ...,
        description="ID категории, которую указал пользователь",
    )
    comment: str | None = Field(
        None,
        max_length=1024,
        description="Комментарий пользователя",
    )

    @field_validator("correct_category_id")
    @classmethod
    def validate_category_id(cls, value: int) -> int:
        """Проверяет, что ID категории положительный."""
        if value <= 0:
            raise ValueError("Category ID must be positive")

        return value


class CategorizationResultResponse(CamelModel):
    """Ответ с результатом классификации транзакции."""

    transaction_id: UUID = Field(..., description="ID транзакции")
    category_id: int = Field(..., description="ID присвоенной категории")
    category_name_snapshot: str = Field(
        ...,
        description="Snapshot имени категории на момент классификации",
    )
    confidence: float = Field(
        ...,
        description="Уверенность модели от 0.0 до 1.0",
    )
    source: str = Field(..., description="Источник классификации")
    model_version: str | None = Field(
        None,
        description="Версия модели, если source=ml",
    )

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, value: float) -> float:
        """Проверяет confidence в диапазоне 0.0-1.0."""
        if not 0.0 <= value <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")

        return value

    @field_validator("category_id")
    @classmethod
    def validate_category_id(cls, value: int) -> int:
        """Проверяет, что ID категории положительный."""
        if value <= 0:
            raise ValueError("Category ID must be positive")

        return value


class HealthResponse(BaseModel):
    """Ответ health endpoint-а."""

    status: str = Field(..., description="Статус сервиса")
    details: dict = Field(default_factory=dict, description="Детали проверки")


class UnifiedSuccessResponse(BaseModel):
    """Единый успешный ответ."""

    ok: bool = Field(True, description="Флаг успешного выполнения")
    detail: str | None = Field(None, description="Детали результата")
