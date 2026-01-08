from decimal import Decimal
from uuid import uuid4

from sqlalchemy import (
    ARRAY, Column, String, DateTime, Index, Date, DECIMAL, 
    func, Integer, ForeignKey
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import validates, relationship

from app.domain.schemas import api as schemas
from app.infrastructure.db.base import Base

class Goal(Base):
    __tablename__ = "goals"

    goal_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    target_value = Column(DECIMAL(12, 2), nullable=False)
    current_value = Column(DECIMAL(12, 2), nullable=False, default=0)
    finish_date = Column(Date, nullable=True)
    tags = Column(ARRAY(String), nullable=False, server_default='{}')
    status = Column(
        String(50), 
        nullable=False, 
        default=schemas.GoalStatus.ONGOING.value
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )
    notification_state = relationship("GoalNotification", uselist=False, back_populates="goal", cascade="all, delete-orphan")

    __table_args__ = (
        Index('ix_goals_status_finish_date', 'status', 'finish_date'),
    )

    @validates('target_value', 'current_value')
    def validate_decimals(self, key, value):
        if not isinstance(value, Decimal):
            value = Decimal(str(value))
        if key == 'target_value' and value <= 0:
            raise ValueError("target_value must be positive")
        if key == 'current_value' and value < 0:
            raise ValueError("current_value must be non-negative")
        return value

class GoalNotification(Base):
    __tablename__ = "goal_notifications"
    
    goal_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("goals.goal_id", ondelete="CASCADE"), 
        primary_key=True
    )
    last_checked_date = Column(DateTime(timezone=True), nullable=True)
    goal = relationship("Goal", back_populates="notification_state")

class ProcessedTransaction(Base):
    __tablename__ = "processed_goal_transactions"

    transaction_id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    goal_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("goals.goal_id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

class OutboxEvent(Base):
    __tablename__ = "outbox_events"

    event_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False)
    topic = Column(String(255), nullable=False)
    event_type = Column(String(255), nullable=False)
    payload = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    retry_count = Column(Integer, default=0, nullable=False)
    status = Column(String(50), default='pending', nullable=False)

    __table_args__ = (
        Index('ix_outbox_created_at', 'created_at'),
    )