import calendar
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4
from sqlalchemy import (
    ARRAY,
    Column,
    Date,
    DateTime,
    DECIMAL,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship, validates

from app.domain.enums import GoalStatus
from app.infrastructure.db.base import Base

class Goal(Base):
    __tablename__ = "goals"

    goal_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False,
    )
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    target_value = Column(DECIMAL(12, 2), nullable=False)
    current_value = Column(DECIMAL(12, 2), nullable=False, default=0)
    finish_date = Column(Date, nullable=True)
    tags = Column(ARRAY(String), nullable=False, server_default="{}")
    status = Column(
        String(50),
        nullable=False,
        default=GoalStatus.ONGOING.value,
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    notification_state = relationship(
        "GoalNotification",
        uselist=False,
        back_populates="goal",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_goals_status_finish_date", "status", "finish_date"),
        Index("ix_goals_tags", "tags", postgresql_using="gin"),
    )

    @validates("target_value", "current_value")
    def validate_decimals(self, key, value):
        if not isinstance(value, Decimal):
            value = Decimal(str(value))

        if key == "target_value" and value <= 0:
            raise ValueError("target_value must be positive")

        if key == "current_value" and value < 0:
            raise ValueError("current_value must be non-negative")

        return value

    @property
    def remaining_amount(self) -> Decimal:
        if self.current_value >= self.target_value:
            return Decimal("0.00")
        return self.target_value - self.current_value

    @property
    def days_left(self) -> int | None:
        if not self.finish_date:
            return None

        today = datetime.now(timezone.utc).date()
        return max((self.finish_date - today).days, 0)

    def calculate_recommended_payment(self) -> Decimal | None:
        """
        Считает рекомендуемый платеж в этом месяце.
        Формула: (Остаток / Всего дней) * Дней до конца месяца
        """
        if not self.finish_date:
            return None

        today = datetime.now(timezone.utc).date()

        if self.finish_date <= today:
            return Decimal("0.00")

        remaining = self.remaining_amount
        if remaining <= 0:
            return Decimal("0.00")

        days_total_left = (self.finish_date - today).days
        if days_total_left == 0: 
             return remaining

        last_day_of_month = calendar.monthrange(today.year, today.month)[1]
        date_end_of_month = today.replace(day=last_day_of_month)
        
        days_left_in_current_month = (date_end_of_month - today).days
        
        days_to_count = min(days_left_in_current_month, days_total_left)
        if days_to_count <= 0:
             return Decimal("0.00")

        daily_need = remaining / Decimal(days_total_left)
        monthly_payment = daily_need * Decimal(days_to_count)

        return monthly_payment.quantize(Decimal("0.01"))

    def check_achievement(self) -> bool:
        if (
            self.status == GoalStatus.ONGOING.value
            and self.current_value >= self.target_value
        ):
            self.status = GoalStatus.ACHIEVED.value
            self.updated_at = datetime.now(timezone.utc)
            return True
        return False

    def revert_achievement_if_needed(self) -> bool:
        if (
            self.status == GoalStatus.ACHIEVED.value
            and self.current_value < self.target_value
        ):
            self.status = GoalStatus.ONGOING.value
            self.updated_at = datetime.now(timezone.utc)
            return True
        return False

class GoalNotification(Base):
    __tablename__ = "goal_notifications"

    goal_id = Column(
        UUID(as_uuid=True),
        ForeignKey("goals.goal_id", ondelete="CASCADE"),
        primary_key=True,
    )
    last_checked_date = Column(DateTime(timezone=True), nullable=True)

    goal = relationship("Goal", back_populates="notification_state")

class ProcessedTransaction(Base):
    __tablename__ = "processed_goal_transactions"

    __table_args__ = (
        {"postgresql_partition_by": "RANGE (created_at)"},
    )

    transaction_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
    )
    goal_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        primary_key=True,
    )

class OutboxEvent(Base):
    __tablename__ = "outbox_events"

    event_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False,
    )
    topic = Column(String(255), nullable=False)
    event_type = Column(String(255), nullable=False)
    payload = Column(JSONB, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    retry_count = Column(Integer, default=0, nullable=False)
    status = Column(String(50), default="pending", nullable=False)
    trace_id = Column(String(255), nullable=True)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_outbox_created_at_status", "created_at", "status"),
        Index("ix_outbox_processing", "status", "next_retry_at"),
    )