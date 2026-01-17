from typing import List
from uuid import UUID
from fastapi import APIRouter, Body, Depends, Path, Query, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api import dependencies
from app.domain.schemas import api as schemas
from app.services.service import GoalService

router = APIRouter(tags=["Goals"])

@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Health check сервиса целей",
)
async def health_check(request: Request) -> dict:
    app = request.app
    status_map = {"db": "unknown", "redis": "unknown"}
    has_error = False

    if not getattr(app.state, "engine", None):
        status_map["db"] = "disconnected"
        has_error = True
    else:
        try:
            async with app.state.engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            status_map["db"] = "ok"
        except Exception:
            status_map["db"] = "failed"
            has_error = True

    if not getattr(app.state, "arq_pool", None):
        status_map["redis"] = "disconnected"
        has_error = True
    else:
        try:
            await app.state.arq_pool.ping()
            status_map["redis"] = "ok"
        except Exception:
            status_map["redis"] = "failed"
            has_error = True

    if has_error:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "error", "components": status_map},
        )

    return {"status": "ok", "components": status_map}

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