import asyncio
import logging
from uuid import UUID
from redis.asyncio import Redis

from app.core.config import settings
from app.core.exceptions import ClassificationResultNotFoundError, CategoryNotFoundError
from app.domain.schemas.kafka import TransactionNeedCategoryEvent
from app.infrastructure.db.uow import UnitOfWork
from app.infrastructure.db.models import Category, ClassificationResult, Feedback, ClassificationSource
from app.domain.schemas import api as api_schemas
from app.services.ml.pipeline import MLPipeline
from app.services.classification.rules import ruleManager

logger = logging.getLogger(__name__)

class ClassificationService:
    """Сервис классификации."""
    def __init__(
        self, 
        uow: UnitOfWork, 
        redis: Redis, 
        ml_pipeline: dict | None = None,
        rules: list[dict] | None = None
    ):
        self.uow = uow
        self.redis = redis
        self.ml_pipeline = ml_pipeline
        self.rules = rules or []

    async def _apply_ml(self, event: TransactionNeedCategoryEvent) -> tuple[int | None, str | None, float, str | None]:
        """Применяет ML классификацию к данным транзакции."""
        if not self.ml_pipeline:
            return None, None, 0.0, None
        
        try:
            data = {
                "merchant": event.merchant,
                "mcc": event.mcc,
                "description": event.description
            }
            cat_id, conf = await MLPipeline.predict_async(
                self.ml_pipeline["model"],
                self.ml_pipeline["vectorizer"],
                self.ml_pipeline["classLabels"],
                data
            )
        except Exception:
            return None, None, 0.0, None

        if conf < settings.ML.ML_CONFIDENCE_THRESHOLD_AUDIT:
            return None, None, conf, self.ml_pipeline["modelVersion"]

        cat = await self.uow.categories.get_by_id(cat_id)
        if not cat:
            return None, None, conf, self.ml_pipeline["modelVersion"]

        return cat_id, cat.name, conf, self.ml_pipeline["modelVersion"]
    
    async def process_batch(self, events: list[TransactionNeedCategoryEvent]):
        """Пакетная обработка транзакций."""
        if not events:
            return

        tx_ids = [e.transaction_id for e in events]
        
        async with self.uow:
            existing_ids = await self.uow.results.get_existing_ids(tx_ids)

            new_events = [e for e in events if e.transaction_id not in existing_ids]
            
            if not new_events:
                return
            
            semaphore = asyncio.Semaphore(10) 
            
            async def _classify(ev):
                async with semaphore:
                    return await self._calculate_classification(ev)

            results_data = await asyncio.gather(*[_classify(ev) for ev in new_events])
            
            for res_model, outbox_data in results_data:
                await self.uow.results.upsert(res_model)
                
                self.uow.outbox.add_event(
                    settings.KAFKA.TOPIC_CLASSIFIED, 
                    outbox_data, 
                    "transaction.classified"
                )
                
                resp = api_schemas.CategorizationResultResponse(
                    transaction_id=res_model.transaction_id,
                    category_id=res_model.category_id,
                    category_name=res_model.category_name,
                    confidence=res_model.confidence,
                    source=res_model.source.value,
                    model_version=res_model.model_version
                )
                await self.redis.set(
                    f"classification:{res_model.transaction_id}", 
                    resp.model_dump_json(), 
                    ex=3600
                )

    async def _calculate_classification(self, event: TransactionNeedCategoryEvent):
        """Внутренняя логика классификации одной транзакции."""
        merchant = event.merchant
        mcc = event.mcc
        desc = event.description or ""
        
        rule_cat_id, rule_cat_name, rule_type = ruleManager.find_match(merchant, mcc, desc)

        final_cat_id = rule_cat_id
        final_cat_name = rule_cat_name
        final_source = ClassificationSource.RULES
        final_conf = 1.0
        final_ver = None
        
        is_weak_rule = rule_type == "mcc"

        if (rule_cat_id is None) or is_weak_rule:
            ml_cat_id, ml_cat_name, ml_conf, ml_ver = await self._apply_ml(event)
            
            if ml_cat_id is not None:
                if rule_cat_id is None or (ml_conf > 0.95 and ml_cat_id != 1):
                    final_cat_id = ml_cat_id
                    final_cat_name = ml_cat_name
                    final_source = ClassificationSource.ML
                    final_conf = ml_conf
                    final_ver = ml_ver

        if final_cat_id is None:
            other = await self.uow.categories.get_by_id(1)
            final_cat_id = 1
            final_cat_name = other.name if other else "Other"
            final_source = ClassificationSource.RULES
            final_conf = 0.0

        result = ClassificationResult(
            transaction_id=event.transaction_id,
            category_id=final_cat_id,
            category_name=final_cat_name,
            confidence=final_conf,
            source=final_source,
            model_version=final_ver,
            merchant=merchant,
            description=desc,
            mcc=mcc
        )
        
        outbox_data = {
            "transaction_id": str(event.transaction_id),
            "category_id": final_cat_id,
            "category_name": final_cat_name
        }
        
        return result, outbox_data
    
    async def get_classification(self, tx_id: UUID) -> api_schemas.CategorizationResultResponse:
        """Получает результат классификации по ID транзакции."""
        cache_key = f"classification:{tx_id}"
        if cached := await self.redis.get(cache_key):
             return api_schemas.CategorizationResultResponse.model_validate_json(cached)
        
        async with self.uow:
            res = await self.uow.results.get_by_transaction_id(tx_id)
            if not res:
                raise ClassificationResultNotFoundError("Not found")
            
            resp = api_schemas.CategorizationResultResponse.from_orm(res)
            await self.redis.set(cache_key, resp.model_dump_json(), ex=3600)
            return resp
    
    async def submit_feedback(self, body: api_schemas.FeedbackRequest) -> tuple[dict, Category]:
        """Обрабатывает обратную связь пользователя."""
        async with self.uow:
            existing = await self.uow.results.get_by_transaction_id(body.transaction_id)
            if not existing:
                raise ClassificationResultNotFoundError("Transaction not found")
            
            correct_cat = await self.uow.categories.get_by_id(body.correct_category_id)
            if not correct_cat:
                raise CategoryNotFoundError("Category not found")

            feedback = Feedback(
                transaction_id=body.transaction_id,
                correct_category_id=body.correct_category_id,
                user_id=body.user_id,
                comment=body.comment
            )
            self.uow.feedback.create(feedback)

            old_name = existing.category_name
            existing.source = ClassificationSource.MANUAL
            existing.category_id = body.correct_category_id
            existing.category_name = correct_cat.name
            existing.confidence = 1.0
            await self.uow.results.upsert(existing)

            event_data = {
                "transaction_id": str(body.transaction_id),
                "old_category": old_name,
                "new_category_id": body.correct_category_id,
                "new_category_name": correct_cat.name
            }
            self.uow.outbox.add_event(
                settings.KAFKA.TOPIC_UPDATED, 
                event_data, 
                "transaction.updated"
            )

            await self.redis.delete(f"classification:{body.transaction_id}")
            
            return event_data, correct_cat