from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import Column, DateTime, Index, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID

from app.infrastructure.db.base import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    transaction_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    account_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    category_id = Column(Integer, nullable=True, index=True)
    date = Column(DateTime(timezone=True), nullable=True)
    value = Column(Numeric(18, 2), nullable=False, default=Decimal("0.00"))
    type = Column(Integer, nullable=False)
    status = Column(Integer, nullable=False)
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
        Index("ix_transactions_user_created", "user_id", "created_at"),
        Index("ix_transactions_filters", "user_id", "category_id", "type", "created_at"),
    )
