from uuid import UUID
from datetime import datetime
from typing import Optional

from app.core.schemas import CamelModel
from app.domain.schemas.api import UserRole

class UserDTO(CamelModel):
    user_id: UUID
    email: str
    name: str
    country: str
    role: UserRole
    is_active: bool
    last_login: Optional[datetime]
    created_at: datetime
    updated_at: datetime

class SessionDTO(CamelModel):
    session_id: UUID
    user_id: UUID
    user_agent: str
    device_name: str
    ip: str
    location: str
    revoked: bool
    is_current: bool = False
    refresh_fingerprint: str
    last_activity: datetime
    expires_at: datetime
    created_at: datetime

