from typing import Any
from uuid import UUID

from fastapi import (
    APIRouter,
    Body,
    Depends,
    HTTPException,
    Path,
    Query,
    Request,
    Response,
    status,
)
from fastapi.responses import ORJSONResponse

from app.api import dependencies, health_helpers
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
    app = request.app
    health_status = {}
    has_error = False

    engine = getattr(app.state, "engine", None)
    db_status, db_ok = await health_helpers.get_db_health(engine)
    health_status["db"] = db_status
    if not db_ok:
        has_error = True

    redis_pool = getattr(app.state, "redis_pool", None)
    redis_status, redis_ok = await health_helpers.get_redis_health(redis_pool)
    health_status["redis"] = redis_status
    if not redis_ok:
        has_error = True

    arq_pool = getattr(app.state, "arq_pool", None)
    arq_status, arq_ok = await health_helpers.get_arq_health(arq_pool)
    health_status["arq"] = arq_status
    if not arq_ok:
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
            schemas.ImportTransactionItem.model_validate(item) for item in raw_items
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
    "/{transaction_id}",
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
    "/{transaction_id}",
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
