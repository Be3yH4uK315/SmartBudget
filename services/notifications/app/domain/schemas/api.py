from pydantic import BaseModel, ConfigDict
from typing import Dict, Any, List, Optional

class NotificationResponse(BaseModel):
    id: str
    createdAt: str
    titleKey: str
    messageKey: str
    type: str
    isRead: bool
    service: str
    props: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(populate_by_name=True)

class PaginatedNotifications(BaseModel):
    total: int
    unreadCount: int
    items: List[NotificationResponse]

class NotificationSettingsResponse(BaseModel):
    locale: str
    emailEnabled: bool
    pushEnabled: bool
    disabledServices: List[str]

class NotificationSettingsUpdate(BaseModel):
    locale: Optional[str] = None
    emailEnabled: Optional[bool] = None
    pushEnabled: Optional[bool] = None
    disabledServices: Optional[List[str]] = None
