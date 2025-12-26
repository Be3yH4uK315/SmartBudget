import logging
import re
from uuid import UUID
from redis.asyncio import Redis

from app import models, schemas, settings, exceptions, unit_of_work
from app.services.ml_service import MLService

logger = logging.getLogger(__name__)

class ClassificationService:
    """Сервис классификации."""
    def __init__(
        self, 
        uow: unit_of_work.UnitOfWork, 
        redis: Redis, 
        ml_pipeline: dict | None = None,
        rules: list[dict] | None = None
    ):
        self.uow = uow
        self.redis = redis

        if ml_pipeline:
            self._model = ml_pipeline.get("model")
            self._vectorizer = ml_pipeline.get("vectorizer")
            self._class_labels = ml_pipeline.get("classLabels")
            self._model_version = ml_pipeline.get("modelVersion")
        else:
            self._model = None
            self._vectorizer = None
            self._class_labels = None
            self._model_version = None

        self._rules = rules or []

    async def _apply_rules(self, merchant: str, mcc: int | None, description: str):
        """Применяет правила классификации по приоритету."""
        transaction_text = f"{merchant} {description}".lower().strip()
        
        for rule in self._rules:
            is_match = False
            pt = rule["pattern_type"]
            pat = rule["pattern"].lower()
            
            if pt == "mcc" and mcc and rule["mcc"] == mcc: is_match = True
            elif pt == "exact" and pat == transaction_text: is_match = True
            elif pt == "contains" and pat in transaction_text: is_match = True
            elif pt == "regex" and "compiled_regex" in rule:
                if rule["compiled_regex"].search(transaction_text): is_match = True
            
            if is_match:
                rule_type_tag = pt
                if pt == "mcc" and rule["priority"] >= 100:
                    rule_type_tag = "mcc_generic"

                return rule["category_id"], rule["category_name"], rule_type_tag
        
        return None, None, None

    async def _apply_ml(self, transaction_data: dict):
        """Применяет ML-модель."""
        if not self._model:
            return None, None, 0.0, None

        try:
            cat_id, conf = await MLService.predict_async(
                self._model, self._vectorizer, self._class_labels, transaction_data
            )
        except Exception:
            return None, None, 0.0, None

        if conf < settings.settings.ML.ML_CONFIDENCE_THRESHOLD_AUDIT:
            return await self._get_fallback(conf, self._model_version)

        if conf < settings.settings.ML.ML_CONFIDENCE_THRESHOLD_AUDIT:
            return None, None, conf, self._model_version

        cat = await self.uow.categories.get_by_id(cat_id)
        if not cat:
            return None, None, conf, self._model_version

        return cat_id, cat.name, conf, self._model_version

    async def _get_fallback(self, conf=0.0, ver=None):
        """Возвращает категорию 'Other' (ID=1)."""
        other = await self.uow.categories.get_by_id(1)
        name = other.name if other else "Other"
        return 1, name, conf, ver
    
    async def get_classification(self, tx_id: UUID) -> schemas.CategorizationResultResponse:
        """Получает классификацию с кэшированием."""
        cache_key = f"classification:{tx_id}"
        cached_res = await self.redis.get(cache_key)
        if cached_res:
            return schemas.CategorizationResultResponse.model_validate_json(cached_res)
        
        async with self.uow:
            res = await self.uow.results.get_by_transaction_id(tx_id)
            if not res:
                raise exceptions.ClassificationResultNotFoundError("Not found")
            
            resp = schemas.CategorizationResultResponse.from_orm(res)
            await self.redis.set(cache_key, resp.model_dump_json(), ex=3600)
            return resp

    async def submit_feedback(self, body: schemas.FeedbackRequest) -> tuple[dict, models.Category]:
        """Обрабатывает обратную связь пользователя."""
        async with self.uow:
            existing = await self.uow.results.get_by_transaction_id(body.transaction_id)
            if not existing:
                raise exceptions.ClassificationResultNotFoundError("Transaction not found")
            
            correct_cat = await self.uow.categories.get_by_id(body.correct_category_id)
            if not correct_cat:
                raise exceptions.CategoryNotFoundError("Category not found")

            feedback = models.Feedback(
                transaction_id=body.transaction_id,
                correct_category_id=body.correct_category_id,
                user_id=body.user_id,
                comment=body.comment
            )
            self.uow.feedback.create(feedback)

            old_name = existing.category_name
            existing.source = models.ClassificationSource.MANUAL
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
                settings.settings.KAFKA.TOPIC_UPDATED, 
                event_data, 
                "transaction.updated"
            )

            await self.redis.delete(f"classification:{body.transaction_id}")
            
            return event_data, correct_cat

    async def process_transaction(self, data: dict) -> tuple[dict, dict] | None:
        """Полная логика обработки транзакции с гибридным подходом (Rules + ML)."""
        try:
            tx_id = UUID(data['transaction_id'])
        except (KeyError, ValueError):
            raise exceptions.InvalidKafkaMessageError("Invalid transaction_id")

        async with self.uow:
            if await self.uow.results.get_by_transaction_id(tx_id):
                return None

            rule_cat_id, rule_cat_name, rule_type = await self._apply_rules(
                data.get('merchant', ''), data.get('mcc'), data.get('description', '')
            )

            final_cat_id = rule_cat_id
            final_cat_name = rule_cat_name
            final_source = models.ClassificationSource.RULES
            final_conf = 1.0
            final_ver = None

            is_weak_rule = rule_type in ['mcc', 'mcc_generic']
            need_ml = (rule_cat_id is None) or is_weak_rule

            if need_ml:
                ml_cat_id, ml_cat_name, ml_conf, ml_ver = await self._apply_ml(data)
                
                if rule_cat_id is None:
                    final_cat_id = ml_cat_id
                    final_cat_name = ml_cat_name
                    final_source = models.ClassificationSource.ML
                    final_conf = ml_conf
                    final_ver = ml_ver

                elif ml_conf > 0.8 and ml_cat_id != 1:
                    final_cat_id = ml_cat_id
                    final_cat_name = ml_cat_name
                    final_source = models.ClassificationSource.ML
                    final_conf = ml_conf
                    final_ver = ml_ver

            if final_cat_id is None:
                final_cat_id, final_cat_name, final_conf, final_ver = await self._get_fallback()
                final_source = models.ClassificationSource.RULES 

            result = models.ClassificationResult(
                transaction_id=tx_id,
                category_id=final_cat_id,
                category_name=final_cat_name,
                confidence=final_conf,
                source=final_source,
                model_version=final_ver,
                merchant=data.get('merchant'),
                description=data.get('description'),
                mcc=data.get('mcc')
            )
            await self.uow.results.upsert(result)

            event_classified = {
                "transaction_id": str(tx_id),
                "category_id": final_cat_id,
                "category_name": final_cat_name
            }
            self.uow.outbox.add_event(
                settings.settings.KAFKA.TOPIC_CLASSIFIED, 
                event_classified, 
                "transaction.classified"
            )
            self.uow.outbox.add_event(
                settings.settings.KAFKA.TOPIC_CLASSIFICATION_EVENTS, 
                event_classified, 
                "budget.classification.events"
            )

            resp_model = schemas.CategorizationResultResponse(
                transaction_id=tx_id, category_id=final_cat_id, category_name=final_cat_name,
                confidence=final_conf, source=final_source.value, model_version=final_ver
            )
            await self.redis.set(f"classification:{tx_id}", resp_model.model_dump_json(), ex=3600)

            return event_classified, event_classified