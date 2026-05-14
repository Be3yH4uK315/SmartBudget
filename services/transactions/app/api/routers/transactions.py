from uuid import UUID

from fastapi import APIRouter, Body, Depends, Path, Query, status

from app.api import dependencies
from app.domain.schemas import api as schemas
from app.services.service import TransactionService

router = APIRouter(tags=["Transactions"])


@router.get(
    "",
    response_model=list[schemas.TransactionResponse],
    response_model_exclude_none=True,
    summary="Получить список транзакций",
)
async def list_transactions(
    filters: dependencies.TransactionFilters = Depends(),
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: TransactionService = Depends(dependencies.get_transaction_service),
):
    """Возвращает список транзакций пользователя с фильтрами."""
    return await service.list_transactions(
        user_id=user_id,
        limit_amount=filters.limit,
        offset=filters.offset,
        category_ids=filters.category_ids,
        occurred_from=filters.occurred_from,
        occurred_to=filters.occurred_to,
        transaction_type=filters.transaction_type,
        amount_from=filters.amount_from,
        amount_to=filters.amount_to,
    )


@router.get(
    "/search",
    response_model=list[schemas.TransactionResponse],
    response_model_exclude_none=True,
    summary="Поиск транзакций",
)
async def search_transactions(
    query: str = Query(..., min_length=1, max_length=255),
    limit: int = Query(10, ge=1, le=100),
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: TransactionService = Depends(dependencies.get_transaction_service),
):
    """Ищет транзакции пользователя по строке."""
    return await service.search_transactions(
        user_id=user_id,
        query=query,
        limit_amount=limit,
    )


@router.get(
    "/{transaction_id}",
    response_model=schemas.TransactionDetailResponse,
    response_model_exclude_none=True,
    summary="Получить транзакцию по ID",
)
async def get_transaction(
    transaction_id: UUID = Path(...),
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: TransactionService = Depends(dependencies.get_transaction_service),
):
    """Возвращает детальную информацию по транзакции."""
    return await service.get_transaction(user_id, transaction_id)


@router.post(
    "/manual",
    response_model=schemas.CreateManualTransactionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать ручную транзакцию",
)
async def create_manual_transaction(
    request: schemas.CreateManualTransactionRequest = Body(...),
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: TransactionService = Depends(dependencies.get_transaction_service),
):
    """Создает ручную транзакцию пользователя."""
    return await service.create_manual_transaction(user_id, request)


@router.post(
    "/import/mock",
    response_model=schemas.ImportMockTransactionsResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Импортировать mock-транзакции",
)
async def import_mock_transactions(
    request: schemas.ImportMockTransactionsRequest = Body(...),
    user_id: UUID | None = Depends(dependencies.get_optional_current_user_id),
    service: TransactionService = Depends(dependencies.get_transaction_service),
):
    """Импортирует одну или несколько mock-транзакций."""
    return await service.import_mock_transactions(request, user_id)


@router.patch(
    "/{transaction_id}",
    response_model=schemas.PatchTransactionCategoryResponse,
    summary="Изменить категорию транзакции",
)
async def patch_category(
    request: schemas.PatchTransactionCategoryRequest = Body(...),
    transaction_id: UUID = Path(...),
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: TransactionService = Depends(dependencies.get_transaction_service),
):
    """Изменяет категорию транзакции."""
    return await service.patch_category(
        user_id=user_id,
        transaction_id=transaction_id,
        request=request,
    )


@router.delete(
    "/{transaction_id}",
    response_model=schemas.DeleteTransactionResponse,
    status_code=status.HTTP_200_OK,
    summary="Удалить транзакцию",
)
async def delete_transaction(
    transaction_id: UUID = Path(...),
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: TransactionService = Depends(dependencies.get_transaction_service),
):
    """Удаляет транзакцию пользователя."""
    return await service.delete_user_transaction(user_id, transaction_id)
