import json
from decimal import Decimal
from datetime import date, datetime
from uuid import UUID
from enum import Enum
from typing import Any

def app_json_serializer(obj: Any) -> Any:
    """Универсальный сериализатор для JSON."""
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, Enum):
        return obj.value
    return str(obj)

def to_json_str(data: Any) -> str:
    """Сериализует объект в строку."""
    return json.dumps(data, default=app_json_serializer, ensure_ascii=False)

def to_json_dict(data: Any, max_depth: int = 10) -> Any:
    """Рекурсивно приводит типы к примитивам."""
    if max_depth <= 0:
        return str(data)
    if isinstance(obj := data, dict):
        return {k: to_json_dict(v, max_depth - 1) for k, v in obj.items()}
    if isinstance(obj, list):
        return [to_json_dict(v, max_depth - 1) for v in obj]
    if isinstance(obj, (Decimal, date, datetime, UUID, Enum)):
        return app_json_serializer(obj)
    return obj