from typing import Any
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, Request, Response, status
from fastapi.responses import ORJSONResponse
from sqlalchemy import text

from app.api import dependencies
from app.domain.schemas import api as schemas
from app.services.service import TransactionService

router = APIRouter(tags=["Transactions"])


@router.get(
    "/health/live",
    status_code=status.HTTP_200_OK,
    summary="Liveness probe",
)
async def liveness_check() -> dict:
    return {"status": "ok"}


@router.get(
    "/health/ready",
    status_code=status.HTTP_200_OK,
    summary="Readiness probe",
)
async def readiness_check(request: Request) -> Response:
    health_status = {
        "db": "unknown",
        "kafka": "unknown",
    }
    has_error = False

    engine = getattr(request.app.state, "engine", None)
    if not engine:
        health_status["db"] = "disconnected"
        has_error = True
    else:
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            health_status["db"] = "ok"
        except Exception:
            health_status["db"] = "failed"
            has_error = True

    producer = getattr(request.app.state, "kafka_producer", None)
    if producer and getattr(producer, "_is_running", False):
        health_status["kafka"] = "ok"
    else:
        health_status["kafka"] = "disconnected"
        has_error = True

    if has_error:
        return ORJSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", "components": health_status},
        )

    return ORJSONResponse(content={"status": "ready", "components": health_status})


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Legacy health check",
)
async def legacy_health_check() -> dict:
    return {"status": "Healthy"}


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
    return await service.list_transactions(
        user_id=user_id,
        limit=filters.limit,
        offset=filters.offset,
        category_ids=filters.category_ids,
        date_from=filters.date_from,
        date_to=filters.date_to,
        transaction_type=filters.transaction_type,
        value_from=filters.value_from,
        value_to=filters.value_to,
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
    return await service.search_transactions(user_id, query, limit)


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
    raw_items = payload if isinstance(payload, list) else [payload]
    try:
        items = [
            schemas.ImportTransactionItem.model_validate(item)
            for item in raw_items
        ]
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid body",
        ) from exc

    return await service.import_mock_transactions(items, user_id)


def _parse_patch_category(payload: Any) -> int | None:
    if isinstance(payload, int) or payload is None:
        return payload
    if isinstance(payload, dict):
        request = schemas.PatchTransactionCategoryRequest.model_validate(payload)
        return request.category_id
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="Payload must be categoryId object, integer, or null",
    )


@router.patch(
    "/edit/{transaction_id}",
    summary="Изменить категорию транзакции",
)
async def patch_category(
    payload: Any = Body(...),
    transaction_id: UUID = Path(...),
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: TransactionService = Depends(dependencies.get_transaction_service),
):
    return await service.patch_category(
        user_id,
        transaction_id,
        _parse_patch_category(payload),
    )


@router.delete(
    "/edit/{transaction_id}",
    status_code=status.HTTP_200_OK,
    summary="Удалить транзакцию",
)
async def delete_transaction(
    transaction_id: UUID = Path(...),
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: TransactionService = Depends(dependencies.get_transaction_service),
):
    await service.delete_user_transaction(user_id, transaction_id)
    return Response(status_code=status.HTTP_200_OK)


@router.get(
    "/goals/{account_id}",
    response_model=list[schemas.TransactionsByMonth],
    response_model_exclude_none=True,
    summary="Получить транзакции цели по месяцам",
)
async def get_goal_transactions(
    account_id: UUID = Path(...),
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: TransactionService = Depends(dependencies.get_transaction_service),
):
    return await service.get_transactions_by_month_for_goal(user_id, account_id)
