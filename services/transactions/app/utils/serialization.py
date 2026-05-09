from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID

import orjson


def to_jsonable(value: Any) -> Any:
    """Рекурсивно приводит значение к JSON-совместимому виду."""
    if isinstance(value, Decimal):
        return float(value)

    if isinstance(value, UUID):
        return str(value)

    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)

        return value.isoformat()

    if isinstance(value, date):
        return value.isoformat()

    if isinstance(value, Enum):
        return value.value

    if isinstance(value, dict):
        return {
            key: to_jsonable(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [
            to_jsonable(item)
            for item in value
        ]

    if isinstance(value, tuple):
        return [
            to_jsonable(item)
            for item in value
        ]

    if isinstance(value, set):
        return [
            to_jsonable(item)
            for item in value
        ]

    return value


def to_json_bytes(value: Any) -> bytes:
    """Сериализует значение в JSON bytes."""
    return orjson.dumps(to_jsonable(value))
