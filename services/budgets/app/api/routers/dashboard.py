from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api import dependencies
from app.domain.schemas import api as schemas
from app.services.service import BudgetService

router = APIRouter(tags=["Budget Dashboard"])


@router.get(
    "/budget",
    response_model=schemas.DashboardBudgetResponse,
    summary="Получение бюджета для главного экрана",
)
async def get_dashboard_budget(
    target_date: date | None = Query(None, alias="month"),
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: BudgetService = Depends(dependencies.get_budget_service),
):
    """Возвращает бюджет для главного экрана."""
    return await service.get_dashboard_budget(user_id, target_date)