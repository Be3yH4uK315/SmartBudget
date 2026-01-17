from typing import List
from uuid import UUID
from fastapi import APIRouter, Body, Depends, Path, Query, Request, Response, status
from fastapi.responses import ORJSONResponse
from sqlalchemy import text

from app.api import dependencies
from app.domain.schemas import api as schemas
from app.services.service import GoalService

router = APIRouter(tags=["Goals"])

@router.get(
    "/health/live",
    status_code=status.HTTP_200_OK,
    summary="Liveness probe"
)
async def liveness_check() -> dict:
    """Легкая проверка."""
    return {"status": "ok"}

@router.get(
    "/health/ready",
    status_code=status.HTTP_200_OK,
    summary="Readiness probe"
)
async def readiness_check(request: Request) -> Response:
    """Тяжелая проверка. Проверяет зависимости."""
    app = request.app
    health_status = {
        "db": "unknown",
        "redis": "unknown",
        "arq": "unknown",
        "kafka": "unknown",
    }
    has_error = False

    engine = getattr(app.state, "engine", None)
    if not engine:
        health_status["db"] = "disconnected"
        has_error = True
    else:
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            health_status["db"] = "ok"
        except Exception:
            health_status["db"] = "failed"
            has_error = True

    arq_pool = getattr(app.state, "arq_pool", None)
    if not arq_pool:
        health_status["arq"] = "disconnected"
        has_error = True
    else:
        try:
            await arq_pool.ping()
            health_status["arq"] = "ok"
        except Exception:
            health_status["arq"] = "failed"
            has_error = True

    kafka_producer = getattr(app.state, "kafka_producer", None)
    if not kafka_producer:
        health_status["kafka"] = "disconnected"
        has_error = True
    else:
        try:
            if kafka_producer._is_running:
                health_status["kafka"] = "ok"
            else:
                health_status["kafka"] = "not_running"
                has_error = True
        except Exception:
            health_status["kafka"] = "failed"
            has_error = True

    if has_error:
        return ORJSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", "components": health_status},
        )

    return ORJSONResponse(content={"status": "ready", "components": health_status})

@router.post(
    "/",
    response_model=schemas.CreateGoalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создание цели",
)
async def create_goal(
    request: schemas.CreateGoalRequest = Body(...),
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: GoalService = Depends(dependencies.get_goal_service),
):
    return await service.create_goal(user_id, request)

@router.get(
    "/main",
    response_model=schemas.MainGoalsResponse,
    summary="Цели для главного экрана",
)
async def get_main_goals(
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: GoalService = Depends(dependencies.get_goal_service),
):
    return await service.get_main_goals(user_id)

@router.get(
    "/",
    response_model=List[schemas.AllGoalsResponse],
    summary="Список целей",
)
async def get_goals(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: GoalService = Depends(dependencies.get_goal_service),
):
    return await service.get_all_goals(user_id, limit, offset)

@router.get(
    "/{goal_id}",
    response_model=schemas.GoalResponse,
    summary="Получение цели",
)
async def get_goal(
    goal_id: UUID = Path(...),
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: GoalService = Depends(dependencies.get_goal_service),
):
    return await service.get_goal_details(user_id, goal_id)

@router.patch(
    "/{goal_id}",
    response_model=schemas.GoalResponse,
    summary="Обновление цели",
)
async def update_goal(
    goal_id: UUID = Path(...),
    request: schemas.GoalPatchRequest = Body(...),
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: GoalService = Depends(dependencies.get_goal_service),
):
    return await service.update_goal(user_id, goal_id, request)