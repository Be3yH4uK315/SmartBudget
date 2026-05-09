from uuid import UUID

from fastapi import APIRouter, Depends, Path

from app.api import dependencies
from app.domain.schemas import api as schemas
from app.services.service import TransactionService

router = APIRouter(tags=["Goal Transactions"])


@router.get(
    "/transactions/{account_id}",
    response_model=list[schemas.TransactionsByMonth],
    response_model_exclude_none=True,
    summary="Получить транзакции цели по месяцам",
)
async def get_goal_transactions(
    account_id: UUID = Path(...),
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: TransactionService = Depends(dependencies.get_transaction_service),
):
    """Возвращает транзакции цели, сгруппированные по месяцам."""
    return await service.get_transactions_by_month_for_goal(user_id, account_id)
