import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ARRAY, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class UserNotificationSettings(Base):
    __tablename__ = "user_notification_settings"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    locale = Column(String(10), default="ru", nullable=False)
    email_enabled = Column(Boolean, default=True, nullable=False)
    push_enabled = Column(Boolean, default=True, nullable=False)
    disabled_services = Column(ARRAY(String), default=list, nullable=False)
    fcm_tokens = Column(JSONB, default=list, nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), unique=True, index=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_notification_settings.user_id", ondelete="CASCADE"), index=True, nullable=False)
    service = Column(String(50), nullable=False) # 'Limit', 'Budget', 'Goals', 'Transactions', 'Security'
    type = Column(String(20), nullable=False)    # 'info', 'success', 'alert', 'warning', 'system'
    title_key = Column(String(100), nullable=False)
    message_key = Column(String(100), nullable=False)
    props = Column(JSONB, default=dict, nullable=False)
    
    is_read = Column(Boolean, default=False, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True, nullable=False)

    __table_args__ = (
        Index("ix_notifications_user_id_is_read_created_at", "user_id", "is_read", "created_at"),
    )
