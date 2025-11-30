from uuid import uuid4
from sqlalchemy import (
    Column, String, Boolean, DateTime, ForeignKey, 
    Integer, Index, UniqueConstraint, Date, DECIMAL
)
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
import enum

from app.base import Base

class GoalStatus(enum.Enum):
    IN_PROGRESS = 'in_progress'
    ACHIEVED = 'achieved'
    EXPIRED = 'expired'
    CLOSED = 'closed'

class Goal(Base):
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
        default=GoalStatus.IN_PROGRESS.value
    )
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )
    last_checked_date = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index('ix_goals_user_id', 'user_id'),
        Index('ix_goals_status_finish_date', 'status', 'finish_date'),
    )