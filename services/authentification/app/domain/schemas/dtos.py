from datetime import datetime
from uuid import UUID

from app.core.schemas import CamelModel
from app.domain.schemas.api import Gender, Language, UserRole


class UserDTO(CamelModel):
    """DTO пользователя для внутреннего слоя приложения."""

    user_id: UUID
    email: str
    name: str
    language: Language
    role: UserRole
    gender: Gender | None = None
    is_active: bool
    last_login: datetime | None
    retention_days: int
    created_at: datetime
    updated_at: datetime


class SessionDTO(CamelModel):
    """DTO пользовательской сессии."""

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
