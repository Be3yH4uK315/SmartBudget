import logging
import re
from uuid import UUID
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from aiocache import cached  
from aiocache.serializers import JsonSerializer 

from app.models import Rule, Category, ClassificationResult, Model
from app.settings import settings
from app.services.ml_service import MLService

logger = logging.getLogger(__name__)

@cached(ttl=3600, key="rules_from_db", serializer=JsonSerializer())
async def get_rules_from_db(db: AsyncSession):
    """
    Асинхронно загружает и кэширует правила из БД.
    Кэш сбрасывается при перезапуске сервиса или истечении TTL.
    """
    logger.info("Cache MISS: Loading rules from database...")
    stmt = await db.execute(
        select(Rule)
        .options(joinedload(Rule.category))
        .order_by(Rule.priority.asc())
    )
    rules_objects = stmt.scalars().all()
    
    return [
        {
            "id": str(rule.id),
            "category_id": str(rule.category_id),
            "category_name": rule.category.name,
            "name": rule.name,
            "pattern": rule.pattern,
            "pattern_type": rule.pattern_type.value,
            "mcc": rule.mcc,
            "priority": rule.priority
        } for rule in rules_objects
    ]

class ClassificationService:
    def __init__(self, db: AsyncSession, redis: Redis, ml_pipeline: dict | None = None):
        """
        Сервис классификации.
        """
        self.db = db
        self.redis = redis
        self._rules = []
        
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
        """Загружает правила из кэша или БД с помощью aiocache."""
        if self._rules:
            return

        self._rules = await get_rules_from_db(self.db)
        logger.info(f"Loaded {len(self._rules)} rules.")

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
                    try:
                        if re.search(pattern, transaction_text):
                            return UUID(rule["category_id"]), rule["category_name"]
                    except re.error as e:
                        logger.error(f"Invalid regex in rule {rule['id']}: {e}")
                        continue
                
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

        category_id_str, confidence = MLService.predict(
            self._model, 
            self._vectorizer, 
            self._class_labels, 
            transaction_data
        )

        model_version = self._model_version
        
        if confidence < settings.ml_confidence_threshold_audit:
            logger.debug(f"ML confidence {confidence:.4f} is too low. Fallback.")
            return await self._get_fallback_category(confidence, model_version)
        
        try:
            category = await self.db.get(Category, UUID(category_id_str))
            if not category:
                logger.error(f"ML predicted non-existent category ID: {category_id_str}. Fallback.")
                return await self._get_fallback_category(confidence, model_version)
        except ValueError as e:
            logger.error(f"Invalid category ID from ML: {e}. Fallback.")
            return await self._get_fallback_category(confidence, model_version)

        if confidence < settings.ml_confidence_threshold_accept:
            logger.info(f"ML classification requires audit (confidence: {confidence:.4f})")
            pass

        return category.id, category.name, confidence, model_version

    async def _get_fallback_category(self, confidence=0.0, model_version=None):
        """Возвращает категорию 'Other'."""
        stmt = await self.db.execute(select(Category).where(Category.name == "Other"))
        other_cat = stmt.scalar_one_or_none()
        
        if other_cat:
            return other_cat.id, other_cat.name, confidence, model_version
        
        return None, "Other", confidence, model_version