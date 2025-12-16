from fastapi import APIRouter, Depends, Body, Path, Request, status, HTTPException
from uuid import UUID
from typing import List
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app import dependencies, schemas, services, exceptions

router = APIRouter(tags=["Goals"])

@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Health check сервиса целей"
)
async def health_check(request: Request):
    """
    Проверяет доступность DB, Redis (ARQ) и Kafka Producer.
    """
    app = request.app
    health_status = {
        "db": "unknown",
        "redis": "unknown",
        "kafka": "unknown"
    }
    has_error = False

    if not getattr(app.state, "db_engine", None):
        health_status["db"] = "disconnected"
        has_error = True
    else:
        try:
            async with app.state.db_engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            health_status["db"] = "ok"
        except Exception as e:
            health_status["db"] = "failed"
            has_error = True

    if not getattr(app.state, "arq_pool", None):
        health_status["redis"] = "disconnected"
        has_error = True
    else:
        try:
            await app.state.arq_pool.ping()
            health_status["redis"] = "ok"
        except Exception as e:
            health_status["redis"] = "failed"
            has_error = True

    if getattr(app.state, "kafka_producer", None):
        health_status["kafka"] = "initialized"
    else:
        health_status["kafka"] = "disconnected"
        has_error = True

    if has_error:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "error",
                "components": health_status
            }
        )

    return {
        "status": "ok",
        "components": health_status
    }

@router.post(
    "/",
    response_model=schemas.CreateGoalResponse,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": schemas.UnifiedErrorResponse}},
    summary="Создание цели"
)
async def create_goal(
    request: schemas.CreateGoalRequest = Body(...),
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: services.GoalService = Depends(dependencies.get_goal_service)
):
    """Создает новую цель для пользователя."""
    try:
        goal = await service.create_goal(user_id, request)
        return schemas.CreateGoalResponse(goal_id=goal.id)
    except exceptions.InvalidGoalDataError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get(
    "/",
    response_model=List[schemas.AllGoalsResponse],
    summary="Получение списка целей"
)
async def get_goals(
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: services.GoalService = Depends(dependencies.get_goal_service)
):
    """Получение списка целей."""
    return await service.get_all_goals(user_id)

@router.get(
    "/{goal_id}",
    response_model=schemas.GoalResponse,
    responses={404: {"model": schemas.UnifiedErrorResponse}},
    summary="Получение цели по ID"
)
async def get_goal(
    goal_id: UUID = Path(..., description="ID цели"),
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: services.GoalService = Depends(dependencies.get_goal_service)
):
    """Получение цели по ID."""
    try:
        goal, days_left = await service.get_goal_details(user_id, goal_id)
        return schemas.GoalResponse(**goal.__dict__, days_left=days_left)
    except exceptions.GoalNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.get(
    "/main",
    response_model=schemas.MainGoalsResponse,
    summary="Получение целей для главного экрана"
)
async def get_main_goals(
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: services.GoalService = Depends(dependencies.get_goal_service)
):
    """Получение целей для главного экрана."""
    goals = await service.get_main_goals(user_id)
    return schemas.MainGoalsResponse(goals=goals)

@router.patch(
    "/{goal_id}",
    response_model=schemas.GoalResponse,
    responses={
        404: {"model": schemas.UnifiedErrorResponse},
        400: {"model": schemas.UnifiedErrorResponse}
    },
    summary="Обновление полей цели"
)
async def update_goal(
    goal_id: UUID = Path(...),
    request: schemas.GoalPatchRequest = Body(...),
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: services.GoalService = Depends(dependencies.get_goal_service)
):
    """Обновление полей цели."""
    try:
        if not request.model_dump(exclude_unset=True):
             raise exceptions.InvalidGoalDataError("At least one field must be provided")
             
        goal, days_left = await service.update_goal(user_id, goal_id, request)
        
        return schemas.GoalResponse(
            **goal.__dict__,
            days_left=days_left
        )
    except exceptions.GoalNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except exceptions.InvalidGoalDataError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))