import logging
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Body, Path, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from redis.asyncio import Redis
from aiokafka import AIOKafkaProducer

from app import dependencies, exceptions, schemas, kafka_producer, settings
from app.services.classification_service import ClassificationService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["API"])

@router.get("/health", response_model=schemas.HealthResponse)
async def healthCheck(
    db: AsyncSession = Depends(dependencies.getDb),
    redis: Redis = Depends(dependencies.getRedis),
    kafka: AIOKafkaProducer = Depends(dependencies.getKafkaProducer)
):
    healthDetails = {"db": "ok", "redis": "ok", "kafka": "ok"}
    status_code = 200

    try:
        await db.execute(select(1))
    except Exception as e:
        healthDetails["db"] = f"error: {str(e)}"
        status_code = 503

    try:
        await redis.ping()
    except Exception as e:
        healthDetails["redis"] = f"error: {str(e)}"
        status_code = 503

    try:
        partitions = await kafka.partitions_for(settings.settings.KAFKA.TOPIC_NEED_CATEGORY)
        if not partitions:
             healthDetails["kafka"] = "error: no partitions found"
             status_code = 503
    except Exception as e:
        healthDetails["kafka"] = f"error: {str(e)}"
        status_code = 503

    if status_code != 200:
        raise HTTPException(status_code=status_code, detail={"status": "unhealthy", "details": healthDetails})

    return schemas.HealthResponse(status="healthy", details=healthDetails)


@router.get(
    "/classification/{transactionId}",
    response_model=schemas.CategorizationResultResponse
)
async def getClassificationResult(
    transactionId: UUID = Path(..., description="ID транзакции"),
    service: ClassificationService = Depends(dependencies.getClassificationService)
):
    """
    Получает результат классификации по ID транзакции (с кэшированием в Redis).
    """
    try:
        classification = await service.getClassification(transactionId)
        return classification
    except exceptions.ClassificationResultNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/feedback",
    response_model=schemas.UnifiedSuccessResponse
)
async def submitFeedback(
    body: schemas.FeedbackRequest = Body(...),
    service: ClassificationService = Depends(dependencies.getClassificationService),
    kafka: AIOKafkaProducer = Depends(dependencies.getKafkaProducer)
):
    """
    Принимает обратную связь от пользователя, обновляет результат и 
    отправляет событие для дообучения.
    """
    try:
        eventData, _correctCategory = await service.submitFeedback(body)

        await kafka_producer.sendKafkaEvent(
            producer=kafka,
            topic=settings.settings.KAFKA.TOPIC_UPDATED,
            eventData=eventData
        )

        return schemas.UnifiedSuccessResponse(ok=True, detail="Feedback submitted")
    except (exceptions.ClassificationResultNotFoundError, exceptions.CategoryNotFoundError) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))