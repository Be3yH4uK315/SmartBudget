from uuid import UUID

from fastapi import APIRouter, Depends

from app.api import dependencies
from app.domain.schemas import api as schemas
from app.services.service import GoalService

router = APIRouter(tags=["Goals Dashboard"])


@router.get(
    "/goals",
    response_model=schemas.MainGoalsResponse,
    summary="Получение целей для главного экрана",
)
async def get_main_goals(
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: GoalService = Depends(dependencies.get_goal_service),
):
    """Возвращает цели для главного экрана пользователя."""
    return await service.get_main_goals(user_id)