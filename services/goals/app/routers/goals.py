from fastapi import APIRouter, Depends, Body, Path, status, HTTPException
from uuid import UUID
from typing import List

from app import dependencies, schemas, services, exceptions

router = APIRouter(
    prefix="/users/{user_id}/goals", 
    tags=["Goals"]
)

@router.post(
    "/",
    response_model=schemas.CreateGoalResponse,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": schemas.UnifiedErrorResponse}}
)
async def create_goal(
    user_id: UUID = Depends(dependencies.get_user_id),
    request: schemas.CreateGoalRequest = Body(...),
    service: services.GoalService = Depends(dependencies.get_goal_service)
):
    """Создает новую цель для пользователя."""
    try:
        goal = await service.create_goal(user_id, request)
        return schemas.CreateGoalResponse(goal_id=goal.id)
    except exceptions.InvalidGoalDataError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get(
    "/{goal_id}",
    response_model=schemas.GoalResponse,
    responses={404: {"model": schemas.UnifiedErrorResponse}}
)
async def get_goal(
    user_id: UUID = Depends(dependencies.get_user_id),
    goal_id: UUID = Path(...),
    service: services.GoalService = Depends(dependencies.get_goal_service)
):
    """Получение конкретной цели."""
    try:
        goal, days_left = await service.get_goal_details(user_id, goal_id)
        return schemas.GoalResponse(
            name=goal.name,
            target_value=goal.target_value,
            current_value=goal.current_value,
            finish_date=goal.finish_date,
            days_left=days_left,
            status=goal.status
        )
    except exceptions.GoalNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.get(
    "/main/",
    response_model=schemas.MainGoalsResponse
)
async def get_main_goals(
    user_id: UUID = Depends(dependencies.get_user_id),
    service: services.GoalService = Depends(dependencies.get_goal_service)
):
    """Получение целей для главного экрана."""
    goals = await service.get_main_goals(user_id)
    response_goals = [
        schemas.MainGoalInfo(
            name=g.name,
            target_value=g.target_value,
            current_value=g.current_value
        ) for g in goals
    ]
    return schemas.MainGoalsResponse(goals=response_goals)

@router.get(
    "/",
    response_model=List[schemas.AllGoalsResponse]
)
async def get_all_goals(
    user_id: UUID = Depends(dependencies.get_user_id),
    service: services.GoalService = Depends(dependencies.get_goal_service)
):
    """Получение всех целей пользователя."""
    goals = await service.get_all_goals(user_id)
    return goals

@router.patch(
    "/{goal_id}",
    response_model=schemas.GoalPatchResponse,
    responses={
        404: {"model": schemas.UnifiedErrorResponse},
        400: {"model": schemas.UnifiedErrorResponse}
    }
)
async def update_goal(
    user_id: UUID = Depends(dependencies.get_user_id),
    goal_id: UUID = Path(...),
    request: schemas.GoalPatchRequest = Body(...),
    service: services.GoalService = Depends(dependencies.get_goal_service)
):
    """Обновление полей цели."""
    try:
        if not request.model_dump(exclude_unset=True):
             raise exceptions.InvalidGoalDataError("At least one field must be provided")
             
        goal = await service.update_goal(user_id, goal_id, request)
        return schemas.GoalPatchResponse(
            goal_id=goal.id,
            name=goal.name,
            target_value=goal.target_value,
            current_value=goal.current_value,
            finish_date=goal.finish_date,
            status=goal.status
        )
    except exceptions.GoalNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except exceptions.InvalidGoalDataError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))