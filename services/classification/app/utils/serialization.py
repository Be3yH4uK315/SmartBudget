import json
from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID

import orjson


def app_json_serializer(value: Any) -> Any:
    """Сериализует нестандартные типы в JSON-compatible значения."""
    if isinstance(value, Decimal):
        return str(value)

    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)

        return value.isoformat()

    if isinstance(value, date):
        return value.isoformat()

    if isinstance(value, UUID):
        return str(value)

    if isinstance(value, Enum):
        return value.value

    return str(value)


def to_json_dict(data: Any, max_depth: int = 10) -> Any:
    """Рекурсивно приводит объект к JSON-compatible структуре."""
    if max_depth <= 0:
        return str(data)

    if isinstance(data, dict):
        return {
            key: to_json_dict(value, max_depth - 1)
            for key, value in data.items()
        }

    if isinstance(data, list):
        return [
            to_json_dict(value, max_depth - 1)
            for value in data
        ]

    if isinstance(data, tuple):
        return [
            to_json_dict(value, max_depth - 1)
            for value in data
        ]

    if isinstance(data, set):
        return [
            to_json_dict(value, max_depth - 1)
            for value in data
        ]

    if isinstance(data, (Decimal, date, datetime, UUID, Enum)):
        return app_json_serializer(data)

    return data


def to_json_str(data: Any) -> str:
    """Сериализует объект в JSON string."""
    return json.dumps(
        to_json_dict(data),
        ensure_ascii=False,
    )


def to_json_bytes(data: Any) -> bytes:
    """Сериализует объект в JSON bytes."""
    return orjson.dumps(to_json_dict(data))
