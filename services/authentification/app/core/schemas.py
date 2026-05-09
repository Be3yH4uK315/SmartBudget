from datetime import datetime

from pydantic import BaseModel, ConfigDict


def to_camel(string: str) -> str:
    """Преобразует snake_case в camelCase."""
    parts = string.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])


class CamelModel(BaseModel):
    """Базовая Pydantic-модель с camelCase alias для API-контрактов."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
        json_encoders={datetime: lambda value: value.isoformat()},
    )
