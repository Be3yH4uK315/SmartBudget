import logging
import json
from uuid import UUID
from datetime import datetime, timedelta, timezone, date
from decimal import Decimal

from sqlalchemy import delete, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app import models, exceptions

logger = logging.getLogger(__name__)

MAX_RETRIES = 5

def _json_serializer(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if isinstance(obj, UUID):
        return str(obj)
    raise TypeError(f"Type {type(obj)} not serializable")

class BaseRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

class CategoryRepository(BaseRepository):
    async def get_by_id(self, category_id: int) -> models.Category | None:
        """Получает категорию по ID."""
        return await self.db.get(models.Category, category_id)
    
    async def get_by_name(self, name: str) -> models.Category | None:
        """Получает категорию по имени."""
        stmt = select(models.Category).where(models.Category.name == name)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

class RuleRepository(BaseRepository):
    async def get_all_active_rules(self) -> list[dict]:
        """
        Загружает все правила и преобразует в список словарей.
        """
        stmt = (
            select(models.Rule)
            .options(selectinload(models.Rule.category))
            .order_by(models.Rule.priority.asc())
        )
        result = await self.db.execute(stmt)
        rules = result.scalars().all()
        
        return [
            {
                "rule_id": str(rule.rule_id),
                "category_id": rule.category_id,
                "category_name": rule.category.name,
                "pattern": rule.pattern,
                "pattern_type": rule.pattern_type.value,
                "mcc": rule.mcc,
                "priority": rule.priority
            }
            for rule in rules
        ]

class ClassificationResultRepository(BaseRepository):
    async def get_by_transaction_id(self, tx_id: UUID) -> models.ClassificationResult | None:
        """Получает результат классификации по ID транзакции."""
        stmt = select(models.ClassificationResult).where(
            models.ClassificationResult.transaction_id == tx_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert(
        self, 
        result: models.ClassificationResult
    ) -> models.ClassificationResult:
        """Использует ON CONFLICT для атомарного upsert."""
        insert_stmt = (
            insert(models.ClassificationResult)
            .values(
                transaction_id=result.transaction_id,
                category_id=result.category_id,
                category_name=result.category_name,
                confidence=result.confidence,
                source=result.source,
                model_version=result.model_version,
                merchant=result.merchant,
                description=result.description,
                mcc=result.mcc,
            )
            .on_conflict_do_update(
                index_elements=[models.ClassificationResult.transaction_id],
                set_={
                    "category_id": result.category_id,
                    "category_name": result.category_name,
                    "confidence": result.confidence,
                    "source": result.source,
                    "model_version": result.model_version,
                    "merchant": result.merchant,
                    "description": result.description,
                    "mcc": result.mcc,
                },
            )
            .returning(models.ClassificationResult)
        )
        result_obj = await self.db.scalar(insert_stmt)
        return result_obj

class FeedbackRepository(BaseRepository):
    def create(self, feedback: models.Feedback) -> models.Feedback:
        """Создает новую обратную связь."""
        self.db.add(feedback)
        return feedback
        
    async def get_training_data(self, days_limit: int = 180) -> list[dict]:
        """Получает данные для обучения (преобразованные в словари)."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_limit)
        stmt = select(
            models.ClassificationResult.merchant, 
            models.ClassificationResult.description, 
            models.ClassificationResult.mcc, 
            models.Feedback.correct_category_id
        ).join(
            models.ClassificationResult, 
            models.Feedback.transaction_id == models.ClassificationResult.transaction_id
        ).where(
            models.Feedback.created_at >= cutoff_date,
            or_(
                models.ClassificationResult.source.in_(
                    [models.ClassificationSource.ML, models.ClassificationSource.MANUAL]
                ),
                models.ClassificationResult.confidence < 0.8
            )
        )
        result = await self.db.execute(stmt)
        return [
            {
                "merchant": row["merchant"],
                "description": row["description"],
                "mcc": row["mcc"],
                "label": int(row["correct_category_id"])
            }
            for row in result.mappings().all()
        ]

class ModelRepository(BaseRepository):
    async def get_active_model(self) -> models.Model | None:
        """Получает активную модель."""
        stmt = select(models.Model).where(models.Model.is_active == True)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
        
    async def get_latest_candidate(self) -> models.Model | None:
        """Получает последнюю кандидат-модель."""
        stmt = (
            select(models.Model)
            .where(models.Model.is_active == False)
            .order_by(models.Model.created_at.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    def create(self, model: models.Model) -> models.Model:
        """Создает новую модель."""
        self.db.add(model)
        return model

    def promote(self, candidate: models.Model, active: models.Model | None):
        """Переводит кандидат в активные, деактивирует старую."""
        if active:
            active.is_active = False
            self.db.add(active)
        candidate.is_active = True
        self.db.add(candidate)

class DatasetRepository(BaseRepository):
    def create(
        self, 
        dataset: models.TrainingDataset
    ) -> models.TrainingDataset:
        """Создает запись о датасете."""
        self.db.add(dataset)
        return dataset
    
    async def get_by_id(self, ds_id: UUID) -> models.TrainingDataset | None:
        """Получает датасет по ID."""
        return await self.db.get(models.TrainingDataset, ds_id)
        
    async def get_latest_ready(self) -> models.TrainingDataset | None:
        """Получает последний готовый датасет."""
        stmt = (
            select(models.TrainingDataset)
            .where(models.TrainingDataset.status == models.TrainingDatasetStatus.READY)
            .order_by(models.TrainingDataset.created_at.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
        
    async def update_status(
        self, 
        dataset: models.TrainingDataset, 
        status: models.TrainingDatasetStatus, 
        metrics: dict
    ):
        """Обновляет статус и метрики датасета."""
        dataset.status = status
        dataset.metrics = metrics
        self.db.add(dataset)

class OutboxRepository(BaseRepository):
    def add_event(self, topic: str, event_data: dict, event_type: str) -> None:
        """Добавляет событие в outbox."""
        try:
            safe_payload = json.loads(json.dumps(event_data, default=_json_serializer))
            event = models.OutboxEvent(
                topic=topic,
                event_type=event_type,
                payload=safe_payload,
                status='pending'
            )
            self.db.add(event)
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"Failed to serialize outbox event: {e}")
            raise exceptions.InvalidKafkaMessageError("Event serialization failed")

    async def get_pending_events(self, limit: int = 100) -> list[models.OutboxEvent]:
        """Получает ожидающие события для отправки в Kafka."""
        query = (
            select(models.OutboxEvent)
            .where(models.OutboxEvent.status == 'pending')
            .order_by(models.OutboxEvent.created_at.asc())
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def delete_events(self, event_ids: list[UUID]) -> None:
        """Удаляет успешно отправленные события из outbox."""
        if not event_ids: return
        stmt = delete(models.OutboxEvent).where(models.OutboxEvent.event_id.in_(event_ids))
        await self.db.execute(stmt)

    async def handle_failed_event(self, event_id: UUID, error_msg: str) -> None:
        """Обрабатывает неудачное событие, увеличивая счетчик попыток и обновляя статус."""
        stmt = select(models.OutboxEvent).where(models.OutboxEvent.event_id == event_id)
        result = await self.db.execute(stmt)
        event = result.scalar_one_or_none()
        if event:
            event.retry_count += 1
            event.last_error = error_msg[:512]
            if event.retry_count >= MAX_RETRIES:
                event.status = 'failed'
            self.db.add(event)