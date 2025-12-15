import enum
import uuid
from sqlalchemy import (
    Column, Float, String, Boolean, DateTime, ForeignKey, Integer, Enum as PgEnum, Index, func
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.orm import relationship

from app import base

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
    
    id = Column(Integer, primary_key=True, autoincrement=False) 
    name = Column(String(255), nullable=False, unique=True)
    description = Column(String(1024), nullable=True)
    keywords = Column(ARRAY(String), default=[])
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

class Rule(base.Base):
    __tablename__ = "rules"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category_id = Column(
        Integer, 
        ForeignKey("categories.id", ondelete="CASCADE"), 
        nullable=False
    )
    name = Column(String(255), nullable=False)
    pattern = Column(String, nullable=False)
    pattern_type = Column(
        PgEnum(
            RulePatternType, 
            name="rule_pattern_type_enum"
        ), 
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
    
    category = relationship("Category")
    
    __table_args__ = (
        Index('ix_rules_priority', priority),
        Index('ix_rules_category_id', category_id),
    )

class ClassificationResult(base.Base):
    __tablename__ = "classification_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(UUID(as_uuid=True), nullable=False, unique=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    category_name = Column(String(255), nullable=False)
    confidence = Column(Float, default=1.0, nullable=False)
    source = Column(
        PgEnum(
            ClassificationSource, 
            name="classification_source_enum"
        ), 
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
    
    category = relationship("Category")
    
    __table_args__ = (
        Index('ix_classification_results_transaction_id', transaction_id, unique=True),
        Index('ix_classification_results_source', source),
    )

class Feedback(base.Base):
    __tablename__ = "feedback"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(UUID(as_uuid=True), nullable=False)
    correct_category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=True)
    comment = Column(String, nullable=True)
    processed = Column(Boolean, default=False, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    
    correct_category = relationship("Category")
    
    __table_args__ = (
        Index('ix_feedback_transaction_id', transaction_id),
        Index('ix_feedback_processed', processed),
    )

class Model(base.Base):
    __tablename__ = "models"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
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
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    version = Column(String(100), nullable=False, unique=True)
    file_path = Column(String(1024), nullable=False)
    status = Column(
        PgEnum(
            TrainingDatasetStatus, 
            name="training_dataset_status_enum"
        ), 
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

