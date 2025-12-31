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
    raise TypeError(f"Type {type(obj)} not serializable")

def to_json_str(data: Any) -> str:
    """Сериализует объект в строку."""
    return json.dumps(data, default=app_json_serializer, ensure_ascii=False)

def to_json_dict(data: Any) -> Any:
    """Рекурсивно приводит типы к примитивам (для сохранения в JSONB)."""
    if isinstance(obj := data, dict):
        return {k: to_json_dict(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [to_json_dict(v) for v in obj]
    if isinstance(obj, (Decimal, date, datetime, UUID, Enum)):
        return app_json_serializer(obj)
    return obj