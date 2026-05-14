from fastapi import APIRouter, Request, status
from fastapi.responses import ORJSONResponse

from app.api import health_helpers
from app.domain.schemas import api as schemas

router = APIRouter(tags=["Health"])


@router.get(
    "/health/live",
    response_model=schemas.HealthCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="Liveness probe",
)
async def liveness_check() -> schemas.HealthCheckResponse:
    """Легкая проверка доступности приложения."""
    return schemas.HealthCheckResponse(status="ok")


@router.get(
    "/health",
    response_model=schemas.HealthCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
)
async def health_check() -> schemas.HealthCheckResponse:
    """Проверка совместимости со старым health endpoint."""
    return schemas.HealthCheckResponse(status="Healthy")


@router.get(
    "/health/ready",
    response_model=schemas.ReadinessResponse,
    status_code=status.HTTP_200_OK,
    summary="Readiness probe",
)
async def readiness_check(request: Request) -> schemas.ReadinessResponse | ORJSONResponse:
    """Проверка готовности приложения и внешних зависимостей."""
    app = request.app
    health_status: dict[str, str] = {}
    has_error = False

    engine = getattr(app.state, "engine", None)
    db_status, db_ok = await health_helpers.get_db_health(engine)
    health_status["db"] = db_status
    has_error = has_error or not db_ok

    redis_pool = getattr(app.state, "redis_pool", None)
    redis_status, redis_ok = await health_helpers.get_redis_health(redis_pool)
    health_status["redis"] = redis_status
    has_error = has_error or not redis_ok

    arq_pool = getattr(app.state, "arq_pool", None)
    arq_status, arq_ok = await health_helpers.get_arq_health(arq_pool)
    health_status["arq"] = arq_status
    has_error = has_error or not arq_ok

    response = schemas.ReadinessResponse(
        status="not_ready" if has_error else "ready",
        components=health_status,
    )

    if has_error:
        return ORJSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=response.model_dump(mode="json", by_alias=True),
        )

    return response
