from typing import List
from uuid import UUID
from fastapi import APIRouter, Body, Depends, Path, Query, Request, Response, status
from fastapi.responses import ORJSONResponse
from sqlalchemy import text

from app.api import dependencies
from app.domain.schemas import api as schemas
from app.services.service import GoalService
from app.api.dependencies import GoalFilters

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
        "arq": "unknown",
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

    if has_error:
        return ORJSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", "components": health_status},
        )

    return ORJSONResponse(content={"status": "ready", "components": health_status})

@router.post(
    "",
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
    summary="Получение целей для главного экрана",
)
async def get_main_goals(
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: GoalService = Depends(dependencies.get_goal_service),
):
    return await service.get_main_goals(user_id)

@router.get(
    "",
    response_model=List[schemas.AllGoalsResponse],
    summary="Получение списка целей с фильтрами",
)
async def get_goals(
    filters: GoalFilters = Depends(),
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: GoalService = Depends(dependencies.get_goal_service),
):
    return await service.get_all_goals(
        user_id=user_id,
        limit=filters.limit,
        offset=filters.offset,
        tags=filters.tags_list,
        priorities=filters.priorities_list,
        is_archived=filters.is_archived
    )

@router.get(
    "/search",
    response_model=List[schemas.GoalSearchResponse],
    summary="Поиск целей",
)
async def search_goals(
    query: str = Query(..., min_length=1, max_length=255),
    limit: int = Query(10, ge=1, le=100),
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: GoalService = Depends(dependencies.get_goal_service),
):
    return await service.search_goals(user_id, query, limit)

@router.get(
    "/{goal_id}",
    response_model=schemas.GoalResponse,
    summary="Получение цели по ID",
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
    summary="Обновление полей цели",
)
async def update_goal(
    goal_id: UUID = Path(...),
    request: schemas.GoalPatchRequest = Body(...),
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: GoalService = Depends(dependencies.get_goal_service),
):
    return await service.update_goal(user_id, goal_id, request)

@router.patch(
    "/{goal_id}/archive",
    response_model=schemas.GoalArchiveResponse,
    summary="Переключение архивного статуса цели",
)
async def update_archived_status(
    goal_id: UUID = Path(..., description="ID цели"),
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: GoalService = Depends(dependencies.get_goal_service),
):
    return await service.toggle_archive_status(user_id, goal_id)

@router.post(
    "/{goal_id}/close",
    response_model=schemas.GoalStatusResponse,
    summary="Принудительное закрытие цели",
)
async def close_goal(
    goal_id: UUID = Path(..., description="ID цели"),
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: GoalService = Depends(dependencies.get_goal_service),
):
    return await service.close_goal(user_id, goal_id)

@router.post(
    "/{goal_id}/restore",
    response_model=schemas.GoalStatusResponse,
    summary="Восстановление цели",
)
async def restore_goal(
    goal_id: UUID = Path(..., description="ID цели"),
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: GoalService = Depends(dependencies.get_goal_service),
):
    return await service.restore_goal(user_id, goal_id)
