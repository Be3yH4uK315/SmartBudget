from uuid import UUID

from fastapi import APIRouter, Body, Depends, Path, Query, status

from app.api import dependencies
from app.api.dependencies import GoalFilters
from app.domain.schemas import api as schemas
from app.services.service import GoalService

router = APIRouter(tags=["Goals"])


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
    """Создает новую цель пользователя."""
    return await service.create_goal(user_id, request)


@router.get(
    "",
    response_model=list[schemas.AllGoalsResponse],
    summary="Получение списка целей с фильтрами",
)
async def get_goals(
    filters: GoalFilters = Depends(),
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: GoalService = Depends(dependencies.get_goal_service),
):
    """Возвращает список целей пользователя с фильтрацией."""
    return await service.get_all_goals(
        user_id=user_id,
        limit=filters.limit,
        offset=filters.offset,
        tags=filters.tags_list,
        priorities=filters.priorities_list,
        is_archived=filters.is_archived,
    )


@router.get(
    "/search",
    response_model=list[schemas.GoalSearchResponse],
    summary="Поиск целей",
)
async def search_goals(
    query: str = Query(..., min_length=1, max_length=255),
    limit: int = Query(10, ge=1, le=100),
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: GoalService = Depends(dependencies.get_goal_service),
):
    """Ищет цели пользователя по текстовому запросу."""
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
    """Возвращает детальную информацию по цели."""
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
    """Обновляет поля цели."""
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
    """Переключает архивный статус цели."""
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
    """Принудительно закрывает цель."""
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
    """Восстанавливает закрытую цель."""
    return await service.restore_goal(user_id, goal_id)