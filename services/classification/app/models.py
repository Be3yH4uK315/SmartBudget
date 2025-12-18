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
    
    categoryId = Column(Integer, primary_key=True, autoincrement=False) 
    name = Column(String(255), nullable=False, unique=True)
    description = Column(String(1024), nullable=True)
    keywords = Column(ARRAY(String), default=[])
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
    
    __table_args__ = (
        Index('ix_categories_keywords_gin', keywords, postgresql_using='gin'),
        Index('ix_categories_name', name),
    )

class Rule(base.Base):
    __tablename__ = "rules"
    
    ruleId = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    categoryId = Column(
        Integer, 
        ForeignKey("categories.categoryId", ondelete="CASCADE"), 
        nullable=False
    )
    name = Column(String(255), nullable=False)
    pattern = Column(String, nullable=False)
    patternType = Column(
        PgEnum(
            RulePatternType, 
            name="rule_pattern_type_enum"
        ), 
        default=RulePatternType.CONTAINS, 
        nullable=False
    )
    mcc = Column(Integer, nullable=True)
    priority = Column(Integer, default=100, nullable=False)
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
    
    category = relationship("Category")
    
    __table_args__ = (
        Index('ix_rules_priority', priority),
        Index('ix_rules_categoryId', categoryId),
    )

class ClassificationResult(base.Base):
    __tablename__ = "classification_results"
    
    classificationResultId = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transactionId = Column(UUID(as_uuid=True), nullable=False, unique=True)
    categoryId = Column(Integer, ForeignKey("categories.categoryId"), nullable=False)
    categoryName = Column(String(255), nullable=False)
    confidence = Column(Float, default=1.0, nullable=False)
    source = Column(
        PgEnum(
            ClassificationSource, 
            name="classification_source_enum"
        ), 
        nullable=False
    )
    modelVersion = Column(String(255), nullable=True)
    merchant = Column(String(255), nullable=True)
    description = Column(String, nullable=True)
    mcc = Column(Integer, nullable=True)
    createdAt = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    
    category = relationship("Category")
    
    __table_args__ = (
        Index('ix_classification_results_transactionId', transactionId, unique=True),
        Index('ix_classification_results_source', source),
    )

class Feedback(base.Base):
    __tablename__ = "feedback"
    
    feedbackId = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transactionId = Column(UUID(as_uuid=True), nullable=False)
    correctCategoryId = Column(Integer, ForeignKey("categories.categoryId"), nullable=False)
    userId = Column(UUID(as_uuid=True), nullable=True)
    comment = Column(String, nullable=True)
    processed = Column(Boolean, default=False, nullable=False)
    createdAt = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    
    correctCategory = relationship("Category")
    
    __table_args__ = (
        Index('ix_feedback_transaction_id', transactionId),
        Index('ix_feedback_processed', processed),
    )

class Model(base.Base):
    __tablename__ = "models"
    
    modelId = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    version = Column(String(100), nullable=False, unique=True)
    path = Column(String(1024), nullable=False)
    metrics = Column(JSONB, nullable=True)
    createdAt = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    isActive = Column(Boolean, default=False, nullable=False)
    
    __table_args__ = (
        Index("ix_models_version", version, unique=True),
        Index("ix_models_createdAt", createdAt.desc()),
        Index(
            "ix_models_active_unique",
            isActive,
            unique=True,
            postgresql_where=(isActive.is_(True)),
        ),
    )

class TrainingDataset(base.Base):
    __tablename__ = "training_datasets"
    
    trainingDatasetId = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    version = Column(String(100), nullable=False, unique=True)
    filePath = Column(String(1024), nullable=False)
    status = Column(
        PgEnum(
            TrainingDatasetStatus, 
            name="training_dataset_status_enum"
        ), 
        default=TrainingDatasetStatus.PENDING, 
        nullable=False
    )
    metrics = Column(JSONB, nullable=True)
    createdAt = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    
    __table_args__ = (
        Index('ix_training_datasets_version', version, unique=True),
        Index(
            'ix_training_datasets_status_created',
            createdAt,
            status,
            postgresql_where=(status == TrainingDatasetStatus.READY),
        ),
    )

