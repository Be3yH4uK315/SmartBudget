from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship, validates
from sqlalchemy.types import DECIMAL

from app.infrastructure.db.base import Base


def _utc_now() -> datetime:
    """Возвращает текущее UTC-время."""
    return datetime.now(timezone.utc)


class Budget(Base):
    """Модель месячного бюджета пользователя."""

    __tablename__ = "budgets"

    budget_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False,
    )
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    month = Column(Date, nullable=False)
    total_income_amount = Column(DECIMAL(18, 2), nullable=False, default=0)
    total_limit_amount = Column(DECIMAL(18, 2), nullable=False, default=0)
    is_auto_renew = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)

    category_limits = relationship(
        "CategoryLimit",
        back_populates="budget",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_budgets_user_id_month", "user_id", "month"),
        UniqueConstraint("user_id", "month", name="uq_budgets_user_id_month"),
    )

    @validates("total_income_amount", "total_limit_amount")
    def validate_budget_decimals(self, key: str, value) -> Decimal:
        """Валидирует денежные поля бюджета."""
        resolved_value = value if isinstance(value, Decimal) else Decimal(str(value))

        if resolved_value < 0:
            raise ValueError(f"{key} must be non-negative")

        return resolved_value


class CategoryLimit(Base):
    """Модель лимита бюджета по категории."""

    __tablename__ = "category_limits"

    category_limit_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False,
    )
    budget_id = Column(
        UUID(as_uuid=True),
        ForeignKey("budgets.budget_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category_id = Column(Integer, nullable=False)
    limit_amount = Column(DECIMAL(18, 2), nullable=False, default=0)
    spent_amount = Column(DECIMAL(18, 2), nullable=False, default=0)
    income_amount = Column(DECIMAL(18, 2), nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)

    budget = relationship("Budget", back_populates="category_limits")

    __table_args__ = (
        Index("ix_category_limits_category_id", "category_id"),
        UniqueConstraint(
            "budget_id",
            "category_id",
            name="uq_category_limits_budget_id_category_id",
        ),
    )

    @validates("limit_amount", "spent_amount", "income_amount")
    def validate_category_decimals(self, key: str, value) -> Decimal:
        """Валидирует денежные поля лимита категории."""
        resolved_value = value if isinstance(value, Decimal) else Decimal(str(value))

        if resolved_value < 0:
            raise ValueError(f"{key} must be non-negative")

        return resolved_value


class ProcessedBudgetTransaction(Base):
    """Обработанная транзакция бюджета для идемпотентности consumer-а."""

    __tablename__ = "processed_budget_transactions"

    transaction_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
    )
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    month = Column(Date, nullable=False, index=True)
    category_id = Column(Integer, nullable=True)
    amount = Column(DECIMAL(18, 2), nullable=False)
    transaction_type = Column(String(50), nullable=False)
    date = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=_utc_now,
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=_utc_now,
        server_default=func.now(),
    )

    __table_args__ = (
        Index("ix_processed_budget_transactions_user_id", "user_id"),
        Index("ix_processed_budget_transactions_category_id", "category_id"),
        Index(
            "ix_processed_budget_transactions_user_month",
            "user_id",
            "month",
        ),
        Index("ix_processed_budget_transactions_occurred_at", "date"),
    )


class OutboxEvent(Base):
    """Outbox-событие для последующей публикации в Kafka."""

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
