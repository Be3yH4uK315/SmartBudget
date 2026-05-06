import logging
from uuid import UUID
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Body,
    Path,
    Request,
    Response,
    status,
)
from fastapi.responses import ORJSONResponse

from app.core.exceptions import ClassificationResultNotFoundError, CategoryNotFoundError
from app.domain.schemas import api as schemas
from app.api import dependencies, health_helpers
from app.services.classification.service import ClassificationService

logger = logging.getLogger(__name__)
router = APIRouter()


async def _collect_readiness_components(
    request: Request,
) -> tuple[dict[str, str], bool]:
    app = request.app
    health_status = {}
    has_error = False

    engine = getattr(app.state, "engine", None)
    db_status, db_ok = await health_helpers.get_db_health(engine)
    health_status["db"] = db_status
    if not db_ok:
        has_error = True

    redis_pool = getattr(app.state, "redis_pool", None)
    redis_status, redis_ok = await health_helpers.get_redis_health(redis_pool)
    health_status["redis"] = redis_status
    if not redis_ok:
        has_error = True

    arq_pool = getattr(app.state, "arq_pool", None)
    arq_status, arq_ok = await health_helpers.get_arq_health(arq_pool)
    health_status["arq"] = arq_status
    if not arq_ok:
        has_error = True

    return health_status, has_error


@router.get(
    "/health/live",
    status_code=status.HTTP_200_OK,
    summary="Liveness probe",
)
async def liveness_check() -> dict[str, str]:
    """Легкая проверка."""
    return {"status": "ok"}


@router.get(
    "/health/ready",
    status_code=status.HTTP_200_OK,
    summary="Readiness probe",
)
async def readiness_check(request: Request) -> Response:
    """Тяжелая проверка. Проверяет зависимости."""
    health_status, has_error = await _collect_readiness_components(request)
    if has_error:
        return ORJSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", "components": health_status},
        )

    return ORJSONResponse(content={"status": "ready", "components": health_status})


@router.get(
    "/classification/{transaction_id}",
    response_model=schemas.CategorizationResultResponse,
)
async def get_classification_result(
    transaction_id: UUID = Path(..., description="ID транзакции"),
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: ClassificationService = Depends(dependencies.get_classification_service),
):
    """Получает результат классификации по ID транзакции (с кэшированием в Redis)."""
    try:
        return await service.get_classification(user_id, transaction_id)
    except ClassificationResultNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/feedback", response_model=schemas.UnifiedSuccessResponse)
async def submit_feedback(
    body: schemas.FeedbackRequest = Body(...),
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: ClassificationService = Depends(dependencies.get_classification_service),
):
    try:
        await service.submit_feedback(user_id, body)
        return schemas.UnifiedSuccessResponse(ok=True, detail="Feedback accepted")
    except (ClassificationResultNotFoundError, CategoryNotFoundError) as e:
        raise HTTPException(status_code=404, detail=str(e))
