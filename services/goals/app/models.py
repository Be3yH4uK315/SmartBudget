from uuid import uuid4
from sqlalchemy import (
    Column, ForeignKey, String, DateTime,
    Index, Date, DECIMAL, func, Integer, JSON
)
from sqlalchemy.dialects.postgresql import UUID
import enum

from app import base

class GoalStatus(enum.Enum):
    ONGOING = 'ongoing'
    ACHIEVED = 'achieved'
    EXPIRED = 'expired'
    CLOSED = 'closed'

class Goal(base.Base):
    __tablename__ = "goals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    name = Column(String(255), nullable=False, default='Название цели')
    target_value = Column(DECIMAL(12, 2), nullable=False)
    current_value = Column(DECIMAL(12, 2), nullable=False, default=0)
    finish_date = Column(Date, nullable=False)
    status = Column(
        String(50), 
        nullable=False, 
        default=GoalStatus.ONGOING.value
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
    )

class ProcessedTransaction(base.Base):
    __tablename__ = "processed_goal_transactions"

    transaction_id = Column(UUID(as_uuid=True), primary_key=True)
    goal_id = Column(UUID(as_uuid=True), ForeignKey("goals.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

class OutboxEvent(base.Base):
    __tablename__ = "outbox_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    topic = Column(String(255), nullable=False)
    event_type = Column(String(255), nullable=False)
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    retry_count = Column(Integer, default=0)
    status = Column(String(50), default='pending')

    __table_args__ = (
        Index('ix_outbox_created_at', 'created_at'),
    )