import calendar
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4
from sqlalchemy import (
    Boolean,
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
from sqlalchemy.dialects.postgresql import JSONB, UUID, ARRAY
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
    target_amount = Column(DECIMAL(18, 2), nullable=False)
    current_amount = Column(DECIMAL(18, 2), nullable=False, default=0)
    finish_date = Column(Date, nullable=True)
    tags = Column(ARRAY(String), nullable=False, default=list)
    priority = Column(String(20), nullable=True)
    is_archived = Column(Boolean, nullable=False, default=False)
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
        Index("ix_goals_main_filter", "user_id", "is_archived", "status", "priority"),
    )

    @validates("target_amount", "current_amount")
    def validate_decimals(self, key, value):
        if not isinstance(value, Decimal):
            value = Decimal(str(value))

        if key == "target_amount" and value <= 0:
            raise ValueError("target_amount must be positive")

        if key == "current_amount" and value < 0:
            raise ValueError("current_amount must be non-negative")

        return value

    @property
    def remaining_amount(self) -> Decimal:
        if self.current_amount >= self.target_amount:
            return Decimal("0.00")
        return self.target_amount - self.current_amount

    @property
    def days_left(self) -> int | None:
        if not self.finish_date:
            return None

        today = datetime.now(timezone.utc).date()
        return max((self.finish_date - today).days, 0)

    def calculate_recommended_payment(
        self,
        net_change_this_month: Decimal = Decimal(0),
    ) -> Decimal | None:
        """Гибридный расчет платежа."""
        if not self.finish_date:
            return None

        today = datetime.now(timezone.utc).date()

        if self.finish_date <= today:
            return Decimal("0.00")

        if self.current_amount >= self.target_amount:
            return Decimal("0.00")

        last_day_of_month = calendar.monthrange(today.year, today.month)[1]
        end_of_month_date = today.replace(day=last_day_of_month)
        period_end_date = min(end_of_month_date, self.finish_date)

        if net_change_this_month >= 0:
            start_of_month = today.replace(day=1)
            calc_start_date = start_of_month
            if self.created_at.date() > start_of_month:
                calc_start_date = self.created_at.date()

            balance_at_start = self.current_amount - net_change_this_month
            balance_at_start = max(balance_at_start, Decimal("0.00"))

            remaining_at_start = self.target_amount - balance_at_start
            if remaining_at_start <= 0:
                return Decimal("0.00")

            total_days_remaining_from_start = (
                self.finish_date - calc_start_date
            ).days
            if total_days_remaining_from_start <= 0:
                return self.target_amount - self.current_amount

            daily_rate = (
                remaining_at_start / Decimal(total_days_remaining_from_start)
            )

            days_in_period = (period_end_date - calc_start_date).days + 1
            if days_in_period <= 0:
                return Decimal("0.00")

            monthly_quota = daily_rate * Decimal(days_in_period)
            recommendation = monthly_quota - net_change_this_month

            return max(
                recommendation,
                Decimal("0.00"),
            ).quantize(Decimal("0.01"))

        else:
            days_total_left = (self.finish_date - today).days
            if days_total_left <= 0:
                return self.remaining_amount

            daily_rate_new = (
                self.remaining_amount / Decimal(days_total_left)
            )

            days_left_in_month = (period_end_date - today).days + 1
            if days_left_in_month <= 0:
                return Decimal("0.00")

            recommendation = daily_rate_new * Decimal(days_left_in_month)

            return recommendation.quantize(Decimal("0.01"))

    def check_achievement(self) -> bool:
        if (
            self.status == GoalStatus.ONGOING.value
            and self.current_amount >= self.target_amount
        ):
            self.status = GoalStatus.ACHIEVED.value
            self.updated_at = datetime.now(timezone.utc)
            return True
        return False

    def revert_achievement_if_needed(self) -> bool:
        if (
            self.status == GoalStatus.ACHIEVED.value
            and self.current_amount < self.target_amount
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
    last_checked_at = Column(DateTime(timezone=True), nullable=True)

    goal = relationship("Goal", back_populates="notification_state")

class ProcessedTransaction(Base):
    __tablename__ = "processed_goal_transactions"

    __table_args__ = (
        Index("ix_processed_goal_transactions_goal_occurred", "goal_id", "occurred_at"),
        {"postgresql_partition_by": "RANGE (created_at)"},
    )

    transaction_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
    )
    goal_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    amount = Column(DECIMAL(18, 2), nullable=False)
    transaction_type = Column(String(50), nullable=False)
    occurred_at = Column(DateTime(timezone=True), nullable=False)
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
