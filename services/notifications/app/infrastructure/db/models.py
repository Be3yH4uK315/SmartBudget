from uuid import uuid4
from sqlalchemy import Boolean, Column, DateTime, String, ForeignKey, Index, func
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship

from app.infrastructure.db.base import Base

class UserNotificationSettings(Base):
    __tablename__ = "user_notification_settings"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    locale = Column(String(10), default="ru", nullable=False)
    notifications_enabled = Column(Boolean, default=True, nullable=False)
    email_enabled = Column(Boolean, default=True, nullable=False)
    push_enabled = Column(Boolean, default=True, nullable=False)
    disabled_services = Column(ARRAY(String), default=list, nullable=False)
    push_subscriptions = Column(JSONB, default=list, nullable=False)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), 
        nullable=False, 
        server_default=func.now(), 
        onupdate=func.now()
    )

    notifications = relationship(
        "Notification", 
        back_populates="settings", 
        cascade="all, delete-orphan"
    )

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False)
    event_id = Column(UUID(as_uuid=True), unique=True, index=True, nullable=False)
    user_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("user_notification_settings.user_id", ondelete="CASCADE"), 
        index=True, 
        nullable=False
    )
    
    service = Column(String(50), nullable=False)
    type = Column(String(20), nullable=False)
    title_key = Column(String(100), nullable=False)
    message_key = Column(String(100), nullable=False)
    props = Column(JSONB, default=dict, nullable=False)
    
    is_read = Column(Boolean, default=False, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    read_at = Column(DateTime(timezone=True), nullable=True)

    settings = relationship("UserNotificationSettings", back_populates="notifications")

    __table_args__ = (
        Index("ix_notifications_user_id_is_read_created_at", "user_id", "is_read", "created_at"),
    )
