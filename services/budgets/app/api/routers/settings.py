from datetime import date
from uuid import UUID

from fastapi import APIRouter, Body, Depends, Query
from fastapi.responses import ORJSONResponse

from app.api import dependencies
from app.domain.schemas import api as schemas
from app.services.service import BudgetService

router = APIRouter(tags=["Budget Settings"])


@router.get(
    "/budget",
    response_model=schemas.BudgetSettingsResponse,
    summary="Получение настроек бюджета",
)
async def get_budget_settings(
    target_date: date | None = Query(None, alias="month"),
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: BudgetService = Depends(dependencies.get_budget_service),
):
    """Возвращает настройки бюджета пользователя."""
    return await service.get_budget_settings(user_id, target_date)


@router.patch(
    "/budget",
    summary="Обновление настроек бюджета",
)
async def patch_budget_settings(
    request: schemas.PatchBudgetRequest = Body(...),
    target_date: date | None = Query(None, alias="month"),
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: BudgetService = Depends(dependencies.get_budget_service),
):
    """Обновляет настройки бюджета пользователя."""
    await service.patch_budget(user_id, request, target_date)

    return ORJSONResponse(content=None)