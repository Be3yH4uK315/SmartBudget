from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID

import orjson


def app_default(obj: Any) -> Any:
    """Преобразует нестандартные Python-типы в JSON-совместимые значения."""
    if isinstance(obj, Decimal):
        return float(obj)

    if isinstance(obj, Enum):
        return obj.value

    if isinstance(obj, set):
        return list(obj)

    if isinstance(obj, UUID):
        return str(obj)

    if isinstance(obj, (date, datetime)):
        return obj.isoformat()

    raise TypeError(f"Type {type(obj)} is not JSON serializable")


def to_json_str(data: Any) -> str:
    """Сериализует данные в JSON-строку."""
    return orjson.dumps(
        data,
        default=app_default,
        option=orjson.OPT_NON_STR_KEYS,
    ).decode("utf-8")


def to_json_bytes(data: Any) -> bytes:
    """Сериализует данные в JSON bytes."""
    return orjson.dumps(
        data,
        default=app_default,
        option=orjson.OPT_NON_STR_KEYS,
    )


def recursive_normalize(obj: Any) -> Any:
    """Рекурсивно приводит объект к JSON-совместимым примитивам."""
    if isinstance(obj, dict):
        return {key: recursive_normalize(value) for key, value in obj.items()}

    if isinstance(obj, list):
        return [recursive_normalize(value) for value in obj]

    if isinstance(obj, tuple):
        return [recursive_normalize(value) for value in obj]

    if isinstance(obj, set):
        return [recursive_normalize(value) for value in obj]

    if isinstance(obj, (Decimal, Enum, UUID, date, datetime)):
        return app_default(obj)

    return obj
