import logging
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Body, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from redis.asyncio import Redis
from aiokafka import AIOKafkaProducer

from app.dependencies import get_db, get_redis, get_kafka_producer
from app.models import ClassificationResult, Feedback, Category
from app.schemas import (
    CategorizationResultResponse, FeedbackRequest, HealthResponse, UnifiedSuccessResponse
)
from app.kafka_producer import send_kafka_event
from app.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter(tags=["API"])

@router.get(
    "/health",
    response_model=HealthResponse
)
async def health_check(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    kafka: AIOKafkaProducer = Depends(get_kafka_producer)
):
    """
    Проверяет состояние сервиса и его зависимостей (DB, Redis, Kafka).
    """
    health_details = {"db": "ok", "redis": "ok", "kafka": "ok"}
    try:
        await db.execute(select(1))
    except Exception as e:
        health_details["db"] = f"error: {e}"
        raise HTTPException(503, detail={"status": "unhealthy", "details": health_details})

    try:
        await redis.ping()
    except Exception as e:
        health_details["redis"] = f"error: {e}"
        raise HTTPException(503, detail={"status": "unhealthy", "details": health_details})

    try:
        await kafka.send_and_wait(settings.topic_classification_events, b'{"healthcheck": "ping"}')
    except Exception as e:
        health_details["kafka"] = f"error: {e}"
        raise HTTPException(503, detail={"status": "unhealthy", "details": health_details})

    return HealthResponse(status="healthy", details=health_details)


@router.get(
    "/classification/{transaction_id}",
    response_model=CategorizationResultResponse
)
async def get_classification_result(
    transaction_id: UUID = Path(..., description="ID транзакции"),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    """
    Получает результат классификации по ID транзакции (с кэшированием в Redis).
    """
    cache_key = f"classification:{transaction_id}"
    try:
        cached_result = await redis.get(cache_key)
        if cached_result:
            logger.debug(f"Cache HIT for transaction {transaction_id}")
            return CategorizationResultResponse.model_validate_json(cached_result)
    except Exception as e:
        logger.warning(f"Redis GET failed for {transaction_id}: {e}. Fetching from DB.")

    logger.debug(f"Cache MISS for transaction {transaction_id}")
    
    result = await db.execute(
        select(ClassificationResult).where(ClassificationResult.transaction_id == transaction_id)
    )
    classification = result.scalar_one_or_none()

    if not classification:
        raise HTTPException(status_code=404, detail="Classification result not found")

    try:
        response_model = CategorizationResultResponse.from_orm(classification)
        await redis.set(
            cache_key, 
            response_model.model_dump_json(), 
            ex=3600
        )
    except Exception as e:
        logger.warning(f"Redis SET failed for {transaction_id}: {e}")

    return response_model


@router.post(
    "/feedback",
    response_model=UnifiedSuccessResponse
)
async def submit_feedback(
    body: FeedbackRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    kafka: AIOKafkaProducer = Depends(get_kafka_producer)
):
    """
    Принимает обратную связь от пользователя, обновляет результат и 
    отправляет событие для дообучения.
    """
    async with db.begin():
        result_stmt = await db.execute(
            select(ClassificationResult).where(ClassificationResult.transaction_id == body.transaction_id)
        )
        existing_result = result_stmt.scalar_one_or_none()
        if not existing_result:
            raise HTTPException(404, "Transaction result to update not found")

        category_stmt = await db.execute(
            select(Category).where(Category.id == body.correct_category_id)
        )
        correct_category = category_stmt.scalar_one_or_none()
        if not correct_category:
            raise HTTPException(400, "Invalid 'correct_category_id' provided")

        new_feedback = Feedback(
            transaction_id=body.transaction_id,
            correct_category_id=body.correct_category_id,
            user_id=body.user_id,
            comment=body.comment,
            processed=False
        )
        db.add(new_feedback)
        
        old_category_name = existing_result.category_name
        existing_result.source = 'manual'
        existing_result.category_id = body.correct_category_id
        existing_result.category_name = correct_category.name
        existing_result.confidence = 1.0

        await db.commit()

    event_data = {
        "transaction_id": str(body.transaction_id),
        "old_category": old_category_name,
        "new_category_id": str(body.correct_category_id),
        "new_category_name": correct_category.name
    }
    
    await send_kafka_event(
        producer=kafka,
        topic=settings.topic_updated,
        event_data=event_data
    )

    return UnifiedSuccessResponse(ok=True, detail="Feedback submitted")