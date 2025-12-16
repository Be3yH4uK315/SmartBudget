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

    goalId = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    userId = Column(UUID(as_uuid=True), nullable=False)
    name = Column(String(255), nullable=False, default='Название цели')
    targetValue = Column(DECIMAL(12, 2), nullable=False)
    currentValue = Column(DECIMAL(12, 2), nullable=False, default=0)
    finishDate = Column(Date, nullable=False)
    status = Column(
        String(50), 
        nullable=False, 
        default=GoalStatus.ONGOING.value
    )
    createdAt = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    updatedAt = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )
    lastCheckedDate = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index('ix_goals_userId', 'userId'),
        Index('ix_goals_status_finishDate', 'status', 'finishDate'),
    )

class ProcessedTransaction(base.Base):
    __tablename__ = "processed_goal_transactions"

    transactionId = Column(UUID(as_uuid=True), primary_key=True)
    goalId = Column(UUID(as_uuid=True), ForeignKey("goals.goalId", ondelete="CASCADE"), nullable=False)
    createdAt = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

class OutboxEvent(base.Base):
    __tablename__ = "outbox_events"

    eventId = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    topic = Column(String(255), nullable=False)
    eventType = Column(String(255), nullable=False)
    payload = Column(JSON, nullable=False)
    createdAt = Column(DateTime(timezone=True), server_default=func.now())
    retryСount = Column(Integer, default=0)
    status = Column(String(50), default='pending')

    __table_args__ = (
        Index('ix_outbox_createdAt', 'createdAt'),
    )