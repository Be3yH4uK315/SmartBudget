import logging
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Body, Path, Request
from sqlalchemy import text

from app.core.exceptions import ClassificationResultNotFoundError, CategoryNotFoundError
from app.domain.schemas import api as schemas
from app.api import dependencies
from app.services.classification.service import ClassificationService

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/health", response_model=schemas.HealthResponse)
async def health_check(request: Request):
    """Проверка здоровья."""
    health = {"db": "unknown", "redis": "unknown"}
    status = "healthy"
    code = 200

    try:
        if getattr(request.app.state, "engine", None):
            async with request.app.state.engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            health["db"] = "ok"
        else:
            health["db"] = "disconnected"
            status = "unhealthy"
            code = 503
    except Exception as e:
        health["db"] = f"error: {str(e)}"
        status = "unhealthy"
        code = 503

    try:
        pool = getattr(request.app.state, "redis_pool", None)
        if pool:
            import redis.asyncio as aioredis
            r = aioredis.Redis(connection_pool=pool)
            await r.ping()
            await r.aclose()
            health["redis"] = "ok"
        else:
            health["redis"] = "disconnected"
            status = "unhealthy"
            code = 503
    except Exception as e:
        health["redis"] = f"error: {str(e)}"
        status = "unhealthy"
        code = 503

    if code != 200:
        raise HTTPException(status_code=code, detail={"status": status, "details": health})
    
    return schemas.HealthResponse(status=status, details=health)

@router.get(
    "/classification/{transaction_id}",
    response_model=schemas.CategorizationResultResponse
)
async def get_classification_result(
    transaction_id: UUID = Path(..., description="ID транзакции"),
    service: ClassificationService = Depends(dependencies.get_classification_service)
):
    """Получает результат классификации по ID транзакции (с кэшированием в Redis)."""
    try:
        return await service.get_classification(transaction_id)
    except ClassificationResultNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post(
    "/feedback",
    response_model=schemas.UnifiedSuccessResponse
)
async def submit_feedback(
    body: schemas.FeedbackRequest = Body(...),
    service: ClassificationService = Depends(dependencies.get_classification_service),
):
    try:
        await service.submit_feedback(body)
        return schemas.UnifiedSuccessResponse(ok=True, detail="Feedback accepted")
    except (ClassificationResultNotFoundError, CategoryNotFoundError) as e:
        raise HTTPException(status_code=404, detail=str(e))