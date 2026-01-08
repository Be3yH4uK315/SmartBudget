from fastapi import APIRouter, Depends, Body, Path, Request, status
from uuid import UUID
from typing import List
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.domain.schemas import api as schemas
from app.api import dependencies
from app.services import service

router = APIRouter(tags=["Goals"])

@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Health check сервиса целей"
)
async def health_check(request: Request) -> dict:
    app = request.app
    health_status = {"db": "unknown", "redis": "unknown"}
    has_error = False

    if not getattr(app.state, "engine", None):
        health_status["db"] = "disconnected"
        has_error = True
    else:
        try:
            async with app.state.engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            health_status["db"] = "ok"
        except Exception:
            health_status["db"] = "failed"
            has_error = True

    if not getattr(app.state, "arq_pool", None):
        health_status["redis"] = "disconnected"
        has_error = True
    else:
        try:
            await app.state.arq_pool.ping()
            health_status["redis"] = "ok"
        except Exception:
            health_status["redis"] = "failed"
            has_error = True

    if has_error:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "error", "components": health_status}
        )

    return {"status": "ok", "components": health_status}

@router.post(
    "/",
    response_model=schemas.CreateGoalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создание цели"
)
async def create_goal(
    request: schemas.CreateGoalRequest = Body(...),
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: service.GoalService = Depends(dependencies.get_goal_service)
):
    response = await service.create_goal(user_id, request)
    return response

@router.get(
    "/main",
    response_model=schemas.MainGoalsResponse,
    summary="Получение целей для главного экрана"
)
async def get_main_goals(
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: service.GoalService = Depends(dependencies.get_goal_service)
):
    response = await service.get_main_goals(user_id)
    return response

@router.get(
    "/",
    response_model=List[schemas.AllGoalsResponse],
    summary="Получение списка целей"
)
async def get_goals(
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: service.GoalService = Depends(dependencies.get_goal_service)
):
    response = await service.get_all_goals(user_id)
    return response

@router.get(
    "/{goal_id}",
    response_model=schemas.GoalResponse,
    summary="Получение цели по ID"
)
async def get_goal(
    goal_id: UUID = Path(..., description="ID цели"),
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: service.GoalService = Depends(dependencies.get_goal_service)
):
    response = await service.get_goal_details(user_id, goal_id)
    return response

@router.patch(
    "/{goal_id}",
    response_model=schemas.GoalResponse,
    summary="Обновление полей цели"
)
async def update_goal(
    goal_id: UUID = Path(...),
    request: schemas.GoalPatchRequest = Body(...),
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: service.GoalService = Depends(dependencies.get_goal_service)
):
    response = await service.update_goal(user_id, goal_id, request)
    return response