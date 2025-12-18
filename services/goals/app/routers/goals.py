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
async def healthCheck(request: Request):
    """
    Проверяет доступность DB, Redis (ARQ) и Kafka Producer.
    """
    app = request.app
    healthStatus = {
        "db": "unknown",
        "redis": "unknown",
        "kafka": "unknown"
    }
    hasError = False

    if not getattr(app.state, "engine", None):
        healthStatus["db"] = "disconnected"
        hasError = True
    else:
        try:
            async with app.state.engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            healthStatus["db"] = "ok"
        except Exception as e:
            healthStatus["db"] = "failed"
            hasError = True

    if not getattr(app.state, "arqPool", None):
        healthStatus["redis"] = "disconnected"
        hasError = True
    else:
        try:
            await app.state.arqPool.ping()
            healthStatus["redis"] = "ok"
        except Exception as e:
            healthStatus["redis"] = "failed"
            hasError = True

    if getattr(app.state, "kafkaProducer", None):
        healthStatus["kafka"] = "initialized"
    else:
        healthStatus["kafka"] = "disconnected"
        hasError = True

    if hasError:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "error",
                "components": healthStatus
            }
        )

    return {
        "status": "ok",
        "components": healthStatus
    }

@router.post(
    "/",
    response_model=schemas.CreateGoalResponse,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": schemas.UnifiedErrorResponse}},
    summary="Создание цели"
)
async def createCoal(
    request: schemas.CreateGoalRequest = Body(...),
    userId: UUID = Depends(dependencies.getCurrentUserId),
    service: services.GoalService = Depends(dependencies.getGoalService)
):
    """Создает новую цель для пользователя."""
    try:
        goal = await service.createGoal(userId, request)
        return schemas.CreateGoalResponse(goalId=goal.goalId)
    except exceptions.InvalidGoalDataError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get(
    "/main",
    response_model=schemas.MainGoalsResponse,
    summary="Получение целей для главного экрана"
)
async def get_main_goals(
    userId: UUID = Depends(dependencies.getCurrentUserId),
    service: services.GoalService = Depends(dependencies.getGoalService)
):
    """Получение целей для главного экрана."""
    goals = await service.getMainGoals(userId)
    return schemas.MainGoalsResponse(goals=goals)

@router.get(
    "/",
    response_model=List[schemas.AllGoalsResponse],
    summary="Получение списка целей"
)
async def getGoals(
    userId: UUID = Depends(dependencies.getCurrentUserId),
    service: services.GoalService = Depends(dependencies.getGoalService)
):
    """Получение списка целей."""
    return await service.getAllGoals(userId)

@router.get(
    "/{goalId}",
    response_model=schemas.GoalResponse,
    responses={404: {"model": schemas.UnifiedErrorResponse}},
    summary="Получение цели по ID"
)
async def get_goal(
    goalId: UUID = Path(..., description="ID цели"),
    userId: UUID = Depends(dependencies.getCurrentUserId),
    service: services.GoalService = Depends(dependencies.getGoalService)
):
    """Получение цели по ID."""
    try:
        goal, daysLeft = await service.getGoalDetails(userId, goalId)
        return schemas.GoalResponse(**goal.__dict__, daysLeft=daysLeft)
    except exceptions.GoalNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.patch(
    "/{goalId}",
    response_model=schemas.GoalResponse,
    responses={
        404: {"model": schemas.UnifiedErrorResponse},
        400: {"model": schemas.UnifiedErrorResponse}
    },
    summary="Обновление полей цели"
)
async def update_goal(
    goalId: UUID = Path(...),
    request: schemas.GoalPatchRequest = Body(...),
    userId: UUID = Depends(dependencies.getCurrentUserId),
    service: services.GoalService = Depends(dependencies.getGoalService)
):
    """Обновление полей цели."""
    try:
        if not request.model_dump(exclude_unset=True):
             raise exceptions.InvalidGoalDataError("At least one field must be provided")
             
        goal, daysLeft = await service.updateGoal(userId, goalId, request)
        
        return schemas.GoalResponse(
            **goal.__dict__,
            daysLeft=daysLeft
        )
    except exceptions.GoalNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except exceptions.InvalidGoalDataError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))