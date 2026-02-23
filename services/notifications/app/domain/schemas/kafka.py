from pydantic import BaseModel, UUID4, Field
from datetime import datetime
from typing import Dict, Any

class IncomingNotificationEvent(BaseModel):
    event_id: UUID4
    event_name: str
    user_id: UUID4
    payload: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
