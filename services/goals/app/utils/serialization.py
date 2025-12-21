import json
from decimal import Decimal
from datetime import date, datetime
from uuid import UUID
from enum import Enum
from typing import Any

def app_json_serializer(obj: Any) -> Any:
    """Универсальный сериализатор для всего проекта."""
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, Enum):
        return obj.value
    raise TypeError(f"Type {type(obj)} not serializable")

def to_json_str(data: Any) -> str:
    """Сериализует объект в JSON строку."""
    return json.dumps(data, default=app_json_serializer, ensure_ascii=False)

def recursive_normalize(obj: Any) -> Any:
    """Рекурсивно приводит типы к примитивам (dict/list/str/float)."""
    if isinstance(obj, dict):
        return {k: recursive_normalize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [recursive_normalize(v) for v in obj]
    if isinstance(obj, (Decimal, date, datetime, UUID, Enum)):
        return app_json_serializer(obj)
    return obj