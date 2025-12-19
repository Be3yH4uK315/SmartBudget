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
async def health_check(
    db: AsyncSession = Depends(dependencies.get_db),
    redis: Redis = Depends(dependencies.get_redis),
    kafka: AIOKafkaProducer = Depends(dependencies.get_kafka_producer)
):
    health_details = {"db": "ok", "redis": "ok", "kafka": "ok"}
    status_code = 200

    try:
        await db.execute(select(1))
    except Exception as e:
        health_details["db"] = f"error: {str(e)}"
        status_code = 503

    try:
        await redis.ping()
    except Exception as e:
        health_details["redis"] = f"error: {str(e)}"
        status_code = 503

    try:
        partitions = await kafka.partitions_for(settings.settings.KAFKA.TOPIC_NEED_CATEGORY)
        if not partitions:
             health_details["kafka"] = "error: no partitions found"
             status_code = 503
    except Exception as e:
        health_details["kafka"] = f"error: {str(e)}"
        status_code = 503

    if status_code != 200:
        raise HTTPException(status_code=status_code, detail={"status": "unhealthy", "details": health_details})

    return schemas.HealthResponse(status="healthy", details=health_details)


@router.get(
    "/classification/{transaction_id}",
    response_model=schemas.CategorizationResultResponse
)
async def get_classification_result(
    transaction_id: UUID = Path(..., description="ID транзакции"),
    service: ClassificationService = Depends(dependencies.get_classification_service)
):
    """
    Получает результат классификации по ID транзакции (с кэшированием в Redis).
    """
    try:
        classification = await service.get_classification(transaction_id)
        return classification
    except exceptions.ClassificationResultNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/feedback",
    response_model=schemas.UnifiedSuccessResponse
)
async def submit_feedback(
    body: schemas.FeedbackRequest = Body(...),
    service: ClassificationService = Depends(dependencies.get_classification_service),
    kafka: AIOKafkaProducer = Depends(dependencies.get_kafka_producer)
):
    """
    Принимает обратную связь от пользователя, обновляет результат и 
    отправляет событие для дообучения.
    """
    try:
        event_data, _correct_category = await service.submit_feedback(body)

        await kafka_producer.send_kafka_event(
            kafka,
            settings.settings.KAFKA.TOPIC_UPDATED,
            event_data
        )

        return schemas.UnifiedSuccessResponse(ok=True, detail="Feedback submitted")
    except (exceptions.ClassificationResultNotFoundError, exceptions.CategoryNotFoundError) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))