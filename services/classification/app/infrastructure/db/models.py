import enum
import uuid
from sqlalchemy import (
    Column, Float, String, Boolean, DateTime, ForeignKey, Integer, 
    Enum as PgEnum, Index, func, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.orm import relationship, validates

from app.infrastructure.db import base

class RulePatternType(str, enum.Enum):
    REGEX = "regex"
    CONTAINS = "contains"
    MCC = "mcc"
    EXACT = "exact"

class ClassificationSource(str, enum.Enum):
    RULES = "rules"
    ML = "ml"
    MANUAL = "manual"

class TrainingDatasetStatus(str, enum.Enum):
    PENDING = "pending"
    BUILDING = "building"
    READY = "ready"
    FAILED = "failed"

class Category(base.Base):
    __tablename__ = "categories"
    
    category_id = Column(Integer, primary_key=True, autoincrement=False, nullable=False)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(String(1024), nullable=True)
    keywords = Column(ARRAY(String), default=list, nullable=False)
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
    
    __table_args__ = (
        Index('ix_categories_keywords_gin', keywords, postgresql_using='gin'),
        Index('ix_categories_name', name),
    )

    @validates('name')
    def validate_name(self, key, value):
        """Валидирует имя категории."""
        if not value or len(value) < 2:
            raise ValueError("Category name must be at least 2 characters")
        return value.strip()

class Rule(base.Base):
    __tablename__ = "rules"
    
    rule_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    category_id = Column(
        Integer, 
        ForeignKey("categories.category_id", ondelete="CASCADE"), 
        nullable=False
    )
    name = Column(String(255), nullable=False)
    pattern = Column(String, nullable=False)
    pattern_type = Column(
        PgEnum(RulePatternType, name="rule_pattern_type_enum"), 
        default=RulePatternType.CONTAINS, 
        nullable=False
    )
    mcc = Column(Integer, nullable=True)
    priority = Column(Integer, default=100, nullable=False)
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
    
    category = relationship("Category", lazy="joined")
    
    __table_args__ = (
        Index('ix_rules_priority', priority),
        Index('ix_rules_category_id', category_id),
        CheckConstraint('priority >= 1 AND priority <= 999', name='ck_rule_priority_range'),
    )

class ClassificationResult(base.Base):
    __tablename__ = "classification_results"
    
    classification_result_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    transaction_id = Column(UUID(as_uuid=True), nullable=False, unique=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.category_id"), nullable=False)
    category_name = Column(String(255), nullable=False)
    confidence = Column(Float, default=1.0, nullable=False)
    source = Column(
        PgEnum(ClassificationSource, name="classification_source_enum"), 
        nullable=False
    )
    model_version = Column(String(255), nullable=True)
    merchant = Column(String(255), nullable=True)
    description = Column(String, nullable=True)
    mcc = Column(Integer, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    
    category = relationship("Category", lazy="joined")
    
    __table_args__ = (
        Index('ix_classification_results_transaction_id', transaction_id, unique=True),
        Index('ix_classification_results_source', source),
        CheckConstraint('confidence >= 0.0 AND confidence <= 1.0', name='ck_confidence_range'),
    )

class Feedback(base.Base):
    __tablename__ = "feedback"
    
    feedback_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    transaction_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    correct_category_id = Column(Integer, ForeignKey("categories.category_id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=True)
    comment = Column(String, nullable=True)
    processed = Column(Boolean, default=False, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    
    correct_category = relationship("Category", lazy="joined")
    
    __table_args__ = (
        Index('ix_feedback_transaction_id', transaction_id),
        Index('ix_feedback_processed', processed),
    )

class Model(base.Base):
    __tablename__ = "models"
    
    model_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    name = Column(String(255), nullable=False)
    version = Column(String(100), nullable=False, unique=True)
    path = Column(String(1024), nullable=False)
    metrics = Column(JSONB, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    is_active = Column(Boolean, default=False, nullable=False)
    
    __table_args__ = (
        Index("ix_models_version", version, unique=True),
        Index("ix_models_created_at", created_at.desc()),
        Index(
            "ix_models_active_unique",
            is_active,
            unique=True,
            postgresql_where=(is_active.is_(True)),
        ),
    )

class TrainingDataset(base.Base):
    __tablename__ = "training_datasets"
    
    training_dataset_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    version = Column(String(100), nullable=False, unique=True)
    file_path = Column(String(1024), nullable=False)
    status = Column(
        PgEnum(TrainingDatasetStatus, name="training_dataset_status_enum"), 
        default=TrainingDatasetStatus.PENDING, 
        nullable=False
    )
    metrics = Column(JSONB, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    
    __table_args__ = (
        Index('ix_training_datasets_version', version, unique=True),
        Index(
            'ix_training_datasets_status_created',
            created_at,
            status,
            postgresql_where=(status == TrainingDatasetStatus.READY),
        ),
    )

class OutboxEvent(base.Base):
    __tablename__ = "outbox_events"

    event_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    topic = Column(String(255), nullable=False)
    event_type = Column(String(255), nullable=False)
    payload = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    retry_count = Column(Integer, default=0, nullable=False)
    status = Column(String(50), default='pending', nullable=False)
    last_error = Column(String(512), nullable=True)

    __table_args__ = (
        Index('ix_outbox_status_created_at', 'status', 'created_at'),
        CheckConstraint('retry_count >= 0', name='ck_retry_count_non_negative'),
    )