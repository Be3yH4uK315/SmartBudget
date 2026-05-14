from datetime import date
from uuid import UUID

from fastapi import APIRouter, Body, Depends, Query, status

from app.api import dependencies
from app.domain.schemas import api as schemas
from app.services.service import BudgetService

router = APIRouter(tags=["Budget"])


@router.get(
    "",
    response_model=schemas.BudgetResponse,
    summary="Получение бюджета",
)
async def get_budget(
    target_date: date | None = Query(None, alias="month"),
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: BudgetService = Depends(dependencies.get_budget_service),
):
    """Возвращает бюджет пользователя за выбранный месяц."""
    return await service.get_budget(user_id, target_date)


@router.post(
    "",
    response_model=schemas.CreateBudgetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создание бюджета",
)
async def create_budget(
    request: schemas.CreateBudgetRequest = Body(...),
    target_date: date | None = Query(None, alias="month"),
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: BudgetService = Depends(dependencies.get_budget_service),
):
    """Создает бюджет пользователя за выбранный месяц."""
    return await service.create_budget(user_id, request, target_date)


@router.post(
    "/backfill",
    response_model=schemas.BackfillBudgetTransactionsResponse,
    status_code=status.HTTP_200_OK,
    summary="Восстановить бюджет по транзакциям",
)
async def backfill_budget_transactions(
    request: schemas.BackfillBudgetTransactionsRequest = Body(...),
    target_date: date | None = Query(None, alias="month"),
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: BudgetService = Depends(dependencies.get_budget_service),
):
    """Идемпотентно применяет переданные транзакции к бюджету."""
    return await service.backfill_transactions(user_id, request, target_date)
