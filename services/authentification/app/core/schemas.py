from pydantic import BaseModel, ConfigDict
from datetime import datetime

def to_camel(string: str) -> str:
    parts = string.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])

class CamelModel(BaseModel):
    """Единая базовая модель для всего приложения."""
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
        json_encoders={datetime: lambda v: v.isoformat()}
    )
