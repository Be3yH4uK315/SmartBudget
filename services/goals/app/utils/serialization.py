import orjson
from decimal import Decimal
from datetime import date, datetime
from uuid import UUID
from enum import Enum
from typing import Any

def app_default(obj: Any) -> Any:
    """Кастомный хук для orjson."""
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, set):
        return list(obj)
    raise TypeError(f"Type {type(obj)} not serializable")

def to_json_str(data: Any) -> str:
    """
    Сериализует объект в JSON строку.
    """
    return orjson.dumps(
        data, 
        default=app_default, 
        option=orjson.OPT_NON_STR_KEYS
    ).decode('utf-8')

def to_json_bytes(data: Any) -> bytes:
    """
    Cразу возвращает bytes. 
    """
    return orjson.dumps(
        data, 
        default=app_default,
        option=orjson.OPT_NON_STR_KEYS
    )

def recursive_normalize(obj: Any) -> Any:
    """
    Рекурсивно приводит типы к примитивам.
    """
    if isinstance(obj, dict):
        return {k: recursive_normalize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [recursive_normalize(v) for v in obj]
    if isinstance(obj, (Decimal, Enum)):
        return app_default(obj)
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if isinstance(obj, UUID):
        return str(obj)
    return obj