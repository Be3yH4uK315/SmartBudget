from enum import Enum
from pydantic import Field, EmailStr
from typing import Optional, Literal
from datetime import datetime
from uuid import UUID

from app.core.schemas import CamelModel

class KafkaTopics(str, Enum):
    AUTH_EVENTS = "auth.events"

class AuthEventTypes(str, Enum):
    USER_REGISTERED = "user.registered"
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_LOGIN_FAILED = "user.login_failed"
    PASSWORD_RESET_STARTED = "user.password_reset_started"
    PASSWORD_RESET_VALIDATED = "user.password_reset_validated"
    PASSWORD_RESET_COMPLETED = "user.password_reset"
    PASSWORD_CHANGED = "user.password_changed"
    VERIFICATION_STARTED = "user.verification_started"
    VERIFICATION_VALIDATED = "user.verification_validated"
    TOKEN_REFRESHED = "user.token_refreshed"
    SESSION_REVOKED = "user.session_revoked"

class BaseAuthEvent(CamelModel):
    event: AuthEventTypes
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class UserEvent(BaseAuthEvent):
    user_id: Optional[UUID] = None
    email: Optional[EmailStr] = None
    ip: Optional[str] = None
    location: Optional[str] = None

class UserRegisteredEvent(UserEvent):
    event: Literal[AuthEventTypes.USER_REGISTERED]
    user_id: UUID
    email: EmailStr
    name: str
