from decimal import Decimal
from uuid import uuid4

from sqlalchemy import (
    Column, String, DateTime, Index, Date, DECIMAL, 
    func, Integer, CheckConstraint, ForeignKey
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import validates

from app import base, schemas

class Goal(base.Base):
    __tablename__ = "goals"

    goal_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    target_value = Column(DECIMAL(12, 2), nullable=False)
    current_value = Column(DECIMAL(12, 2), nullable=False, default=0)
    finish_date = Column(Date, nullable=False)
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
    last_checked_date = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index('ix_goals_user_id', 'user_id'),
        Index('ix_goals_status_finish_date', 'status', 'finish_date'),
        CheckConstraint('target_value > 0', name='ck_goal_target_value_positive'),
        CheckConstraint('current_value >= 0', name='ck_goal_current_value_non_negative'),
    )

    @validates("status")
    def validate_status(self, _, value):
        allowed = {s.value for s in schemas.GoalStatus}
        if value not in allowed:
            raise ValueError("Invalid goal status")
        return value
    
    @validates('target_value', 'current_value')
    def validate_decimal_values(self, key, value):
        """Валидирует значения перед сохранением."""
        if not isinstance(value, Decimal):
            value = Decimal(str(value))
        if key == 'target_value' and value <= 0:
            raise ValueError("target_value must be positive")
        if key == 'current_value' and value < 0:
            raise ValueError("current_value must be non-negative")
        return value

class ProcessedTransaction(base.Base):
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

class OutboxEvent(base.Base):
    __tablename__ = "outbox_events"

    event_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False)
    topic = Column(String(255), nullable=False)
    event_type = Column(String(255), nullable=False)
    payload = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    retry_count = Column(Integer, default=0, nullable=False)
    status = Column(String(50), default='pending', nullable=False)

    __table_args__ = (
        Index('ix_outbox_status_created_at', 'status', 'created_at'),
        CheckConstraint('retry_count >= 0', name='ck_retry_count_non_negative'),
    )