from typing import Any
from uuid import UUID

from fastapi import (
    APIRouter,
    Body,
    Depends,
    HTTPException,
    Path,
    Query,
    Response,
    status,
)

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
        limit_amount=filters.limit_amount,
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
    limit_amount: int = Query(10, ge=1, le=100, alias="limitAmount"),
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: TransactionService = Depends(dependencies.get_transaction_service),
):
    """Ищет транзакции пользователя по строке."""
    return await service.search_transactions(
        user_id=user_id,
        query=query,
        limit_amount=limit_amount,
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
    summary="Импортировать mock-транзакции",
)
async def import_mock_transactions(
    payload: Any = Body(...),
    user_id: UUID | None = Depends(dependencies.get_optional_current_user_id),
    service: TransactionService = Depends(dependencies.get_transaction_service),
):
    """Импортирует одну или несколько mock-транзакций."""
    raw_items = payload if isinstance(payload, list) else [payload]

    try:
        items = [
            schemas.ImportTransactionItem.model_validate(item) for item in raw_items
        ]
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid body",
        ) from exc

    return await service.import_mock_transactions(items, user_id)


@router.patch(
    "/{transaction_id}",
    summary="Изменить категорию транзакции",
)
async def patch_category(
    payload: Any = Body(...),
    transaction_id: UUID = Path(...),
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: TransactionService = Depends(dependencies.get_transaction_service),
):
    """Изменяет категорию транзакции."""
    return await service.patch_category(
        user_id,
        transaction_id,
        _parse_patch_category(payload),
    )


@router.delete(
    "/{transaction_id}",
    status_code=status.HTTP_200_OK,
    summary="Удалить транзакцию",
)
async def delete_transaction(
    transaction_id: UUID = Path(...),
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: TransactionService = Depends(dependencies.get_transaction_service),
):
    """Удаляет транзакцию пользователя."""
    await service.delete_user_transaction(user_id, transaction_id)

    return Response(status_code=status.HTTP_200_OK)


def _parse_patch_category(payload: Any) -> int | None:
    """Извлекает category_id из PATCH payload."""
    if isinstance(payload, int) or payload is None:
        return payload

    if isinstance(payload, dict):
        request = schemas.PatchTransactionCategoryRequest.model_validate(payload)
        return request.category_id

    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="Payload must be categoryId object, integer, or null",
    )
