from fastapi import APIRouter, Request, Response, status
from fastapi.responses import ORJSONResponse

from app.api import health_helpers

router = APIRouter(tags=["health"])


@router.get("/health/live", status_code=status.HTTP_200_OK, summary="Liveness probe")
async def liveness_check() -> dict[str, str]:
    """Легкая проверка доступности приложения."""
    return {"status": "ok"}


@router.get("/health/ready", status_code=status.HTTP_200_OK, summary="Readiness probe")
async def readiness_check(request: Request) -> Response:
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

    if has_error:
        return ORJSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", "components": health_status},
        )

    return ORJSONResponse(
        content={"status": "ready", "components": health_status},
    )
