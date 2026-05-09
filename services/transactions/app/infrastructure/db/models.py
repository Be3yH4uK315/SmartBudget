from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import CheckConstraint, Column, DateTime, Index, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.infrastructure.db.base import Base


class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    account_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    category_id = Column(Integer, nullable=True, index=True)
    occurred_at = Column(DateTime(timezone=True), nullable=False)
    amount = Column(Numeric(18, 2), nullable=False, default=Decimal("0.00"))
    transaction_type = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False)
    merchant = Column(String(500), nullable=False, default="")
    mcc = Column(Integer, nullable=True)
    description = Column(String(2000), nullable=False, default="")
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    imported_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

    __table_args__ = (
        Index("ix_transactions_user_occurred", "user_id", "occurred_at"),
        Index(
            "ix_transactions_filters_v2",
            "user_id",
            "category_id",
            "transaction_type",
            "occurred_at",
        ),
        CheckConstraint("amount >= 0", name="ck_transactions_amount_non_negative"),
        CheckConstraint(
            "transaction_type IN ('income', 'expense')",
            name="ck_transactions_transaction_type_allowed",
        ),
        CheckConstraint(
            "status IN ('rejected', 'confirmed', 'pending')",
            name="ck_transactions_status_allowed",
        ),
    )


class OutboxEvent(Base):
    __tablename__ = "outbox_events"

    event_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False)
    topic = Column(String(255), nullable=False)
    event_type = Column(String(255), nullable=False)
    payload = Column(JSONB, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    retry_count = Column(Integer, default=0, nullable=False)
    status = Column(String(50), default="pending", nullable=False)
    trace_id = Column(String(255), nullable=True)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_outbox_created_at_status", "created_at", "status"),
        Index("ix_outbox_processing", "status", "next_retry_at"),
    )
