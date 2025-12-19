import logging
import re
from uuid import UUID
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from aiocache import cached
from aiocache.serializers import JsonSerializer

from app import models, schemas, settings, exceptions, repositories
from app.services.ml_service import MLService

logger = logging.getLogger(__name__)

@cached(ttl=3600, key="rules_config_v1", serializer=JsonSerializer())
async def get_cached_rules_as_dict(db: AsyncSession) -> list[dict]:
    """
    Загружает правила из БД и кэширует как словари.
    Преобразование в словари избегает DetachedInstanceError.
    """
    return await repositories.RuleRepository.get_all_active_rules(db)

class ClassificationService:
    def __init__(self, db: AsyncSession, redis: Redis, ml_pipeline: dict | None = None):
        """Сервис классификации."""
        self.db = db
        self.redis = redis
        self.category_repository = repositories.CategoryRepository(db)
        self.result_repository = repositories.ClassificationResultRepository(db)
        self.feedback_repository = repositories.FeedbackRepository(db)
        
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
        self._rules = []

    async def _load_rules(self):
        """Загружает правила из кэша или БД."""
        if self._rules:
            return

        rules_dicts = await get_cached_rules_as_dict(self.db)
        compiled_rules = []
        
        for rule_dict in rules_dicts:
            rule = rule_dict.copy()
            
            if rule["pattern_type"] == "regex":
                try:
                    rule["compiled_regex"] = re.compile(rule["pattern"], re.IGNORECASE)
                except re.error as e:
                    logger.error(f"Invalid regex in rule {rule['rule_id']}: {e}. Skipping.")
                    continue 
            
            compiled_rules.append(rule)

        self._rules = compiled_rules

    async def apply_rules(self, merchant: str, mcc: int | None, description: str) -> tuple[int | None, str | None]:
        """Применяет правила классификации по приоритету."""
        await self._load_rules()
        
        if not self._rules:
            logger.debug("No rules loaded. Returning None.")
            return None, None
        
        transaction_text = f"{merchant} {description}".lower().strip()
        
        for rule in self._rules:
            pattern_type = rule["pattern_type"]
            pattern = rule["pattern"].lower()
            
            is_match = False
            
            if pattern_type == "mcc" and mcc is not None and rule["mcc"] == mcc:
                is_match = True
            elif pattern_type == "exact" and pattern == transaction_text:
                is_match = True
            elif pattern_type == "contains" and pattern in transaction_text:
                is_match = True
            elif pattern_type == "regex" and "compiled_regex" in rule:
                if rule["compiled_regex"].search(transaction_text):
                    is_match = True
            
            if is_match:
                return rule["category_id"], rule["category_name"]
                
        return None, None

    async def apply_ml(self, transaction_data: dict) -> tuple[int | None, str | None, float, str | None]:
        """Применяет ML-модель."""
        if not self._model:
            logger.debug("No ML model loaded. Using fallback.")
            return await self._get_fallback_category()

        try:
            category_id, confidence = await MLService.predict_async(
                self._model, 
                self._vectorizer, 
                self._class_labels, 
                transaction_data
            )
        except Exception as e:
            logger.error(f"Error during ML prediction: {e}")
            return await self._get_fallback_category()

        model_version = self._model_version
        
        if confidence < settings.settings.ML.ML_CONFIDENCE_THRESHOLD_AUDIT:
            logger.debug(f"ML confidence {confidence:.4f} below audit threshold. Using fallback.")
            return await self._get_fallback_category(confidence, model_version)
        
        try:
            category = await self.category_repository.get_by_id(category_id)
            if not category:
                logger.error(f"ML predicted non-existent category: {category_id}. Using fallback.")
                return await self._get_fallback_category(confidence, model_version)
        except Exception as e:
            logger.error(f"Error fetching category {category_id}: {e}. Using fallback.")
            return await self._get_fallback_category(confidence, model_version)

        if confidence < settings.settings.ML.ML_CONFIDENCE_THRESHOLD_ACCEPT:
            logger.info(f"ML classification requires audit (confidence: {confidence:.4f})")

        return category_id, category.name, confidence, model_version

    async def _get_fallback_category(self, confidence: float = 0.0, model_version: str | None = None):
        """Возвращает категорию 'Other' (ID=0)."""
        try:
            other_cat = await self.category_repository.get_by_id(0)
            if other_cat:
                return other_cat.category_id, other_cat.name, confidence, model_version
        except Exception as e:
            logger.error(f"Error getting fallback category: {e}")
        
        return 0, "Other", confidence, model_version
    
    async def get_classification(self, tx_id: UUID) -> schemas.CategorizationResultResponse:
        """Получает классификацию с кэшированием."""
        cache_key = f"classification:{tx_id}"
        cached_result = await self.redis.get(cache_key)
        
        if cached_result:
            return schemas.CategorizationResultResponse.model_validate_json(cached_result)
        
        classification = await self.result_repository.get_by_transaction_id(tx_id)
        if not classification:
            raise exceptions.ClassificationResultNotFoundError("Classification not found")

        response_model = schemas.CategorizationResultResponse.from_orm(classification)
        await self.redis.set(
            cache_key, 
            response_model.model_dump_json(), 
            ex=3600
        )

        return response_model

    async def submit_feedback(self, body: schemas.FeedbackRequest) -> tuple[dict, models.Category]:
        """Обрабатывает обратную связь пользователя."""
        existing_result = await self.result_repository.get_by_transaction_id(body.transaction_id)
        if not existing_result:
            raise exceptions.ClassificationResultNotFoundError("Transaction result not found")

        correct_category = await self.category_repository.get_by_id(body.correct_category_id)
        if not correct_category:
            raise exceptions.CategoryNotFoundError(f"Invalid category ID: {body.correct_category_id}")

        new_feedback = models.Feedback(
            transaction_id=body.transaction_id,
            correct_category_id=body.correct_category_id,
            user_id=body.user_id,
            comment=body.comment,
            processed=False
        )
        await self.feedback_repository.create(new_feedback)
        
        old_category_name = existing_result.category_name
        
        existing_result.source = models.ClassificationSource.MANUAL
        existing_result.category_id = body.correct_category_id
        existing_result.category_name = correct_category.name
        existing_result.confidence = 1.0
        
        await self.result_repository.create_or_update(existing_result)
        
        await self.redis.delete(f"classification:{body.transaction_id}")
        
        event_data = {
            "transaction_id": str(body.transaction_id),
            "old_category": old_category_name,
            "new_category_id": str(body.correct_category_id),
            "new_category_name": correct_category.name
        }
        return event_data, correct_category

    async def process_transaction(self, data: dict) -> tuple[dict, dict] | None:
        """Полная логика обработки транзакции."""
        try:
            transaction_id = UUID(data['transaction_id'])
        except (KeyError, ValueError) as e:
            raise exceptions.InvalidKafkaMessageError(f"Invalid transaction_id: {e}")

        existing = await self.result_repository.get_by_transaction_id(transaction_id)
        if existing:
            logger.info(f"Transaction {transaction_id} already processed. Skipping.")
            return None

        category_id, category_name = await self.apply_rules(
            merchant=data.get('merchant', ''),
            mcc=data.get('mcc'),
            description=data.get('description', '')
        )
        
        source = models.ClassificationSource.RULES
        confidence = 1.0
        model_version = None

        if category_id is None:
            category_id, category_name, confidence, model_version = await self.apply_ml(data)
            source = models.ClassificationSource.ML

        result = models.ClassificationResult(
            transaction_id=transaction_id,
            category_id=category_id,
            category_name=category_name,
            confidence=confidence,
            source=source,
            model_version=model_version,
            merchant=data.get('merchant', ''),
            description=data.get('description', ''),
            mcc=data.get('mcc')
        )
        await self.result_repository.create_or_update(result)

        response_model = schemas.CategorizationResultResponse(
            transaction_id=transaction_id,
            category_id=category_id,
            category_name=category_name,
            confidence=confidence,
            source=source.value,
            model_version=model_version
        )
        await self.redis.set(
            f"classification:{transaction_id}", 
            response_model.model_dump_json(), 
            ex=3600
        )

        event_classified = {
            "transaction_id": str(transaction_id),
            "category_id": category_id,
            "category_name": category_name
        }
        
        event_events = event_classified.copy()
        
        return event_classified, event_events