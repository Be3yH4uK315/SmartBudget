import logging
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Body, Path, Request
from sqlalchemy import text

from app import dependencies, exceptions, schemas
from app.services.classification_service import ClassificationService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["API"])

@router.get("/health", response_model=schemas.HealthResponse)
async def health_check(request: Request):
    app = request.app
    health_details = {"db": "unknown", "redis": "unknown"}
    status_code = 200

    if not getattr(app.state, "engine", None):
        health_details["db"] = "disconnected"
        status_code = 503
    else:
        try:
            async with app.state.engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            health_details["db"] = "ok"
        except Exception as e:
            health_details["db"] = f"error: {str(e)}"
            status_code = 503

    if not getattr(app.state, "redis_pool", None):
        health_details["redis"] = "disconnected"
        status_code = 503
    else:
        try:
            import redis.asyncio as aioredis
            r = aioredis.Redis(connection_pool=app.state.redis_pool)
            await r.ping()
            await r.aclose()
            health_details["redis"] = "ok"
        except Exception as e:
            health_details["redis"] = f"error: {str(e)}"
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
        response = await service.get_classification(transaction_id)
        return response
    except exceptions.ClassificationResultNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/feedback",
    response_model=schemas.UnifiedSuccessResponse
)
async def submit_feedback(
    body: schemas.FeedbackRequest = Body(...),
    service: ClassificationService = Depends(dependencies.get_classification_service),
):
    """
    Принимает обратную связь от пользователя, обновляет результат и 
    отправляет событие для дообучения.
    """
    try:
        await service.submit_feedback(body)
        return schemas.UnifiedSuccessResponse(ok=True, detail="Feedback submitted")
    except (exceptions.ClassificationResultNotFoundError, exceptions.CategoryNotFoundError) as e:
        raise HTTPException(status_code=404, detail=str(e))