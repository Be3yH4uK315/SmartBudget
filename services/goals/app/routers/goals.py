from fastapi import APIRouter, Depends, Body, Path, Query, status, HTTPException
from uuid import UUID
from typing import List, Optional

from app import dependencies, schemas, services, exceptions

router = APIRouter(tags=["Goals"])

@router.post(
    "/",
    response_model=schemas.CreateGoalResponse,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": schemas.UnifiedErrorResponse}}
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
    response_model=List[schemas.AllGoalsResponse] | schemas.GoalResponse,
    responses={404: {"model": schemas.UnifiedErrorResponse}}
)
async def get_goals(
    goal_id: Optional[UUID] = Query(None, description="Получить конкретную цель по ID"),
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: services.GoalService = Depends(dependencies.get_goal_service)
):
    """
    Универсальный метод:
    - Если передан ?goal_id=..., возвращает одну цель.
    - Если goal_id не передан, возвращает список всех целей.
    """
    if goal_id:
        try:
            goal, days_left = await service.get_goal_details(user_id, goal_id)
            return schemas.GoalResponse(**goal.__dict__, days_left=days_left)
        except exceptions.GoalNotFoundError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    else:
        return await service.get_all_goals(user_id)

@router.get(
    "/main",
    response_model=schemas.MainGoalsResponse
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
    }
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