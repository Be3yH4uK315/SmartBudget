import asyncio
import logging
import re
import json
from uuid import UUID
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from aiocache import cached
from aiocache.serializers import JsonSerializer

from app import models, schemas, settings, exceptions, repositories
from app.services.ml_service import MLService

logger = logging.getLogger(__name__)

@cached(ttl=3600, key="rules_from_db", serializer=JsonSerializer())
async def get_cached_rules(db: AsyncSession):
    """Кэширует вызов репозитория."""
    return await repositories.RuleRepository.get_all_active_rules(db)

class ClassificationService:
    def __init__(self, db: AsyncSession, redis: Redis, ml_pipeline: dict | None = None):
        """
        Сервис классификации.
        """
        self.db = db
        self.redis = redis
        self.category_repo = repositories.CategoryRepository(db)
        self.result_repo = repositories.ClassificationResultRepository(db)
        self.feedback_repo = repositories.FeedbackRepository(db)
        
        if ml_pipeline:
            self._model = ml_pipeline.get("model")
            self._vectorizer = ml_pipeline.get("vectorizer")
            self._class_labels = ml_pipeline.get("class_labels")
            self._model_version = ml_pipeline.get("model_version")
        else:
            self._model = None
            self._vectorizer = None
            self._class_labels = None
            self._model_version = None

    async def _load_rules(self):
        """Загружает правила из кэша или БД."""
        if self._rules:
            return

        rules_objects = await get_cached_rules(self.db)
        
        processed_rules = []
        for rule in rules_objects:
            rule_dict = {
                "id": str(rule.id),
                "category_id": str(rule.category_id),
                "category_name": rule.category.name,
                "pattern": rule.pattern,
                "pattern_type": rule.pattern_type.value,
                "mcc": rule.mcc,
                "priority": rule.priority
            }
            if rule.pattern_type.value == "regex":
                try:
                    rule_dict["compiled_regex"] = re.compile(rule.pattern, re.IGNORECASE)
                except re.error as e:
                    logger.error(f"Invalid regex in rule {rule.id}: {e}. Rule disabled.")
                    continue 
            processed_rules.append(rule_dict)

        self._rules = processed_rules
        logger.debug(f"Loaded {len(self._rules)} rules.")

    async def apply_rules(self, merchant: str, mcc: int | None, description: str) -> tuple[UUID | None, str | None]:
        """
        Применяет правила классификации по приоритету.
        Возвращает (category_id, category_name) если match, иначе (None, None).
        """
        await self._load_rules()
        
        if not self._rules:
            logger.warning("No rules loaded. Skipping rules application.")
            return None, None
        
        transaction_text = f"{merchant} {description}".lower()
        
        try:
            for rule in sorted(self._rules, key=lambda r: r["priority"]):
                pattern_type = rule["pattern_type"]
                pattern = rule["pattern"].lower()
                
                if pattern_type == "mcc" and mcc is not None and rule["mcc"] == mcc:
                    return UUID(rule["category_id"]), rule["category_name"]
                
                elif pattern_type == "exact" and pattern == transaction_text:
                    return UUID(rule["category_id"]), rule["category_name"]
                
                elif pattern_type == "contains" and pattern in transaction_text:
                    return UUID(rule["category_id"]), rule["category_name"]
                
                elif pattern_type == "regex":
                    if "compiled_regex" in rule and rule["compiled_regex"].search(transaction_text):
                        return UUID(rule["category_id"]), rule["category_name"]
                
            logger.debug("No rules matched for transaction.")
            return None, None
        
        except Exception as e:
            logger.error(f"Error applying rules: {e}")
            return None, None

    async def apply_ml(self, transaction_data: dict) -> tuple[UUID | None, str | None, float, str | None]:
        """
        Применяет ML-модель, если правила не сработали.
        Возвращает (category_id, category_name, confidence, model_version).
        """
        if not self._model:
            logger.warning("No ML model loaded. ML classification disabled. Falling back.")
            return await self._get_fallback_category()

        loop = asyncio.get_running_loop()

        try:
            category_id_str, confidence = await loop.run_in_executor(
                None, 
                MLService.predict,
                self._model, 
                self._vectorizer, 
                self._class_labels, 
                transaction_data
            )
        except Exception as e:
            logger.error(f"Error during ML prediction execution: {e}")
            return await self._get_fallback_category()

        model_version = self._model_version
        
        if confidence < settings.settings.ml.ml_confidence_threshold_audit:
            logger.debug(f"ML confidence {confidence:.4f} is too low. Fallback.")
            return await self._get_fallback_category(confidence, model_version)
        
        try:
            category = await self.db.get(models.Category, UUID(category_id_str))
            if not category:
                logger.error(f"ML predicted non-existent category ID: {category_id_str}. Fallback.")
                return await self._get_fallback_category(confidence, model_version)
        except ValueError as e:
            logger.error(f"Invalid category ID from ML: {e}. Fallback.")
            return await self._get_fallback_category(confidence, model_version)

        if confidence < settings.settings.ml.ml_confidence_threshold_accept:
            logger.info(f"ML classification requires audit (confidence: {confidence:.4f})")
            pass

        return category.id, category.name, confidence, model_version

    async def _get_fallback_category(self, confidence=0.0, model_version=None):
        """Возвращает категорию 'Other' из репозитория."""
        other_cat = await self.category_repo.get_by_name("Other")
        if other_cat:
            return other_cat.id, other_cat.name, confidence, model_version
        return None, "Other", confidence, model_version
    
    async def get_classification(self, tx_id: UUID) -> models.ClassificationResult:
        """Логика для GET /classification/{id}, перенесено из api.py"""
        cache_key = f"classification:{tx_id}"
        try:
            cached_result = await self.redis.get(cache_key)
            if cached_result:
                logger.debug(f"Cache HIT for transaction {tx_id}")
                return schemas.CategorizationResultResponse.model_validate_json(cached_result)
        except Exception as e:
            logger.warning(f"Redis GET failed for {tx_id}: {e}. Fetching from DB.")

        logger.debug(f"Cache MISS for transaction {tx_id}")
        
        classification = await self.result_repo.get_by_transaction_id(tx_id)
        if not classification:
            raise exceptions.ClassificationResultNotFoundError("Classification result not found")

        try:
            response_model = schemas.CategorizationResultResponse.from_orm(classification)
            await self.redis.set(
                cache_key, 
                response_model.model_dump_json(), 
                ex=3600
            )
        except Exception as e:
            logger.warning(f"Redis SET failed for {tx_id}: {e}")

        return response_model

    async def submit_feedback(self, body: schemas.FeedbackRequest) -> tuple[dict, models.Category]:
        """Логика для POST /feedback, перенесено из api.py"""
        existing_result = await self.result_repo.get_by_transaction_id(body.transaction_id)
        if not existing_result:
            raise exceptions.ClassificationResultNotFoundError("Transaction result to update not found")

        correct_category = await self.category_repo.get_by_id(body.correct_category_id)
        if not correct_category:
            raise exceptions.CategoryNotFoundError("Invalid 'correct_category_id' provided")

        new_feedback = models.Feedback(
            transaction_id=body.transaction_id,
            correct_category_id=body.correct_category_id,
            user_id=body.user_id,
            comment=body.comment,
            processed=False
        )
        await self.feedback_repo.create(new_feedback)
        
        old_category_name = existing_result.category_name
        existing_result.source = models.ClassificationSource.MANUAL
        existing_result.category_id = body.correct_category_id
        existing_result.category_name = correct_category.name
        existing_result.confidence = 1.0

        await self.result_repo.create_or_update(existing_result)
        
        event_data = {
            "transaction_id": str(body.transaction_id),
            "old_category": old_category_name,
            "new_category_id": str(body.correct_category_id),
            "new_category_name": correct_category.name
        }
        return event_data, correct_category

    async def process_transaction(self, data: dict) -> tuple[dict, dict] | None:
        """
        Полная логика обработки из consumers.py.
        Возвращает (event_data_classified, event_data_events) или None.
        """
        try:
            transaction_id = UUID(data['transaction_id'])
        except (KeyError, ValueError):
            raise exceptions.InvalidKafkaMessageError(f"Invalid transaction_id: {data.get('transaction_id')}")
        
        existing = await self.result_repo.get_by_transaction_id(transaction_id)
        if existing:
            logger.warning(f"Transaction {transaction_id} already processed. Skipping.")
            return None

        category_id, category_name = await self.apply_rules(
            merchant=data.get('merchant', ''),
            mcc=data.get('mcc'),
            description=data.get('description', '')
        )
        
        source = models.ClassificationSource.RULES
        confidence = 1.0
        model_version = None

        if not category_id:
            category_id, category_name, confidence, model_version = await self.apply_ml(data)
            source = models.ClassificationSource.ML

        if not category_id:
            logger.error(f"Failed to classify transaction {transaction_id} even with fallback.")
            return None

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
        await self.result_repo.create_or_update(result)
        
        try:
            await self.redis.set(
                f"classification:{transaction_id}", 
                json.dumps({"category_name": category_name, "category_id": str(category_id)}),
                ex=3600
            )
        except Exception as e:
            logger.warning(f"Redis SET failed: {e}")

        event_data = {
            "transaction_id": str(transaction_id),
            "category_id": str(category_id),
            "category_name": category_name
        }
        return event_data, event_data