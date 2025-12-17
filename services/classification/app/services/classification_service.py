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
async def getCachedRulesAsDict(db: AsyncSession) -> list[dict]:
    """
    Загружает правила из БД и преобразует их в список словарей.
    Это необходимо для корректной работы JSON-кэша и избежания DetachedInstanceError.
    """
    rulesObjects = await repositories.RuleRepository.getAllActiveRules(db)
    
    processedRules = []
    for rule in rulesObjects:
        ruleDict = {
            "ruleId": str(rule.ruleId),
            "categoryId": rule.categoryId,
            "categoryName": rule.category.name,
            "pattern": rule.pattern,
            "patternType": rule.patternType.value,
            "mcc": rule.mcc,
            "priority": rule.priority
        }
        processedRules.append(ruleDict)
    
    return processedRules

class ClassificationService:
    def __init__(self, db: AsyncSession, redis: Redis, mlPipeline: dict | None = None):
        """
        Сервис классификации.
        """
        self.db = db
        self.redis = redis
        self.categoryReposity = repositories.CategoryRepository(db)
        self.resultReposity = repositories.ClassificationResultRepository(db)
        self.feedbackReposity = repositories.FeedbackRepository(db)
        
        if mlPipeline:
            self._model = mlPipeline.get("model")
            self._vectorizer = mlPipeline.get("vectorizer")
            self._class_labels = mlPipeline.get("class_labels")
            self._model_version = mlPipeline.get("modelVersion")
        else:
            self._model = None
            self._vectorizer = None
            self._class_labels = None
            self._model_version = None
        self._rules = []

    async def _loadRules(self):
        """Загружает правила из кэша или БД."""
        if self._rules:
            return

        rulesDicts = await getCachedRulesAsDict(self.db)

        compiledRules = []
        for rDict in rulesDicts:
            rule = rDict.copy()
            
            if rule["patternType"] == "regex":
                try:
                    rule["compiled_regex"] = re.compile(rule["pattern"], re.IGNORECASE)
                except re.error as e:
                    logger.error(f"Invalid regex in rule {rule['id']}: {e}. Rule disabled.")
                    continue 
            compiledRules.append(rule)

        self._rules = compiledRules

    async def applyRules(self, merchant: str, mcc: int | None, description: str) -> tuple[int | None, str | None]:
        """
        Применяет правила классификации по приоритету.
        Возвращает (categoryId, categoryName) если match, иначе (None, None).
        """
        await self._loadRules()
        
        if not self._rules:
            logger.warning("No rules loaded. Skipping rules application.")
            return None, None
        
        transactionText = f"{merchant} {description}".lower()
        
        for rule in sorted(self._rules, key=lambda r: r["priority"]):
            patternType = rule["patternType"]
            pattern = rule["pattern"].lower()
            
            isMatch = False
            
            if patternType == "mcc" and mcc is not None and rule["mcc"] == mcc:
                isMatch = True
            elif patternType == "exact" and pattern == transactionText:
                isMatch = True
            elif patternType == "contains" and pattern in transactionText:
                isMatch = True
            elif patternType == "regex" and "compiled_regex" in rule:
                if rule["compiled_regex"].search(transactionText):
                    isMatch = True
            
            if isMatch:
                return rule["categoryId"], rule["categoryName"]
                
        return None, None

    async def applyMl(self, transactionData: dict) -> tuple[int | None, str | None, float, str | None]:
        """
        Применяет ML-модель, если правила не сработали.
        Возвращает (categoryId, categoryName, confidence, modelVersion).
        """
        if not self._model:
            logger.warning("No ML model loaded. ML classification disabled. Falling back.")
            return await self._getFallbackCategory()

        try:
            categoryId, confidence = await MLService.predict_async(
                self._model, 
                self._vectorizer, 
                self._class_labels, 
                transactionData
            )
        except Exception as e:
            logger.error(f"Error during ML prediction execution: {e}")
            return await self._getFallbackCategory()

        modelVersion = self._model_version
        
        if confidence < settings.settings.ML.ML_CONFIDENCE_THRESHOLD_AUDIT:
            logger.debug(f"ML confidence {confidence:.4f} is too low. Fallback.")
            return await self._getFallbackCategory(confidence, modelVersion)
        
        try:
            category = await self.db.get(models.Category, categoryId)
            if not category:
                logger.error(f"ML predicted non-existent category ID: {categoryId}. Fallback.")
                return await self._getFallbackCategory(confidence, modelVersion)
        except Exception as e:
            logger.error(f"DB Error fetching category {categoryId}: {e}")
            return await self._getFallbackCategory(confidence, modelVersion)

        if confidence < settings.settings.ML.ML_CONFIDENCE_THRESHOLD_ACCEPT:
            logger.info(f"ML classification requires audit (confidence: {confidence:.4f})")
            pass

        return category.categoryId, category.name, confidence, modelVersion

    async def _getFallbackCategory(self, confidence=0.0, modelVersion=None):
        """Возвращает категорию 'Other' (ID=0)."""
        otherCat = await self.categoryReposity.getById(0)
        if otherCat:
            return otherCat.categoryId, otherCat.name, confidence, modelVersion
        
        return 0, "Other", confidence, modelVersion
    
    async def getClassification(self, txId: UUID) -> schemas.CategorizationResultResponse:
        cacheKey = f"classification:{txId}"
        cachedResult = await self.redis.get(cacheKey)
        if cachedResult:
            return schemas.CategorizationResultResponse.model_validate_json(cachedResult)
        
        classification = await self.resultReposity.getByTransactionId(txId)
        if not classification:
            raise exceptions.ClassificationResultNotFoundError("Classification result not found")

        responseModel = schemas.CategorizationResultResponse.from_orm(classification)
        await self.redis.set(
            cacheKey, 
            responseModel.model_dump_json(), 
            ex=3600
        )

        return responseModel

    async def submitFeedback(self, body: schemas.FeedbackRequest) -> tuple[dict, models.Category]:
        """Логика для POST /feedback, перенесено из api.py"""
        existingResult = await self.resultReposity.getByTransactionId(body.transactionId)
        if not existingResult:
            raise exceptions.ClassificationResultNotFoundError("Transaction result to update not found")

        correctCategory = await self.categoryReposity.getById(body.correctCategoryId)
        if not correctCategory:
            raise exceptions.CategoryNotFoundError(f"Invalid 'correctCategoryId' {body.correctCategoryId}")

        newFeedback = models.Feedback(
            transactionId=body.transactionId,
            correctCategoryId=body.correctCategoryId,
            userId=body.userId,
            comment=body.comment,
            processed=False
        )
        await self.feedbackReposity.create(newFeedback)
        
        oldCategoryName = existingResult.categoryName
        
        existingResult.source = models.ClassificationSource.MANUAL
        existingResult.categoryId = body.correctCategoryId
        existingResult.categoryName = correctCategory.name
        existingResult.confidence = 1.0
        
        await self.resultReposity.createOrUpdate(existingResult)
        
        await self.redis.delete(f"classification:{body.transactionId}")
        
        eventData = {
            "transactionId": str(body.transactionId),
            "oldCategory": oldCategoryName,
            "newCategoryId": str(body.correctCategoryId),
            "newCategoryName": correctCategory.name
        }
        return eventData, correctCategory

    async def processTransaction(self, data: dict) -> tuple[dict, dict] | None:
        """
        Полная логика обработки из consumers.py.
        Возвращает (event_data_classified, event_data_events) или None.
        """
        try:
            transactionId = UUID(data['transactionId'])
        except (KeyError, ValueError):
            raise exceptions.InvalidKafkaMessageError(f"Invalid transactionId: {data.get('transactionId')}")

        existing = await self.resultReposity.getByTransactionId(transactionId)
        if existing:
            logger.warning(f"Transaction {transactionId} already processed. Skipping.")
            return None

        categoryId, categoryName = await self.applyRules(
            merchant=data.get('merchant', ''),
            mcc=data.get('mcc'),
            description=data.get('description', '')
        )
        
        source = models.ClassificationSource.RULES
        confidence = 1.0
        modelVersion = None

        if categoryId is None:
            categoryId, categoryName, confidence, modelVersion = await self.applyMl(data)
            source = models.ClassificationSource.ML

        result = models.ClassificationResult(
            transactionId=transactionId,
            categoryId=categoryId,
            categoryName=categoryName,
            confidence=confidence,
            source=source,
            modelVersion=modelVersion,
            merchant=data.get('merchant', ''),
            description=data.get('description', ''),
            mcc=data.get('mcc')
        )
        await self.resultReposity.createOrUpdate(result)

        responseModel = schemas.CategorizationResultResponse(
            transactionId=transactionId,
            categoryId=categoryId,
            categoryName=categoryName,
            confidence=confidence,
            source=source.value,
            modelVersion=modelVersion
        )
        await self.redis.set(
            f"classification:{transactionId}", 
            responseModel.model_dump_json(), 
            ex=3600
        )

        eventClassified = {
            "transactionId": str(transactionId),
            "categoryId": categoryId,
            "categoryName": categoryName
        }
        
        eventEvents = eventClassified.copy()
        
        return eventClassified, eventEvents