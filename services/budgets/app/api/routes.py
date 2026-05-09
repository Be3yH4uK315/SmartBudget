from datetime import date
from uuid import UUID

from fastapi import (
    APIRouter,
    Body,
    Depends,
    Query,
    Request,
    Response,
    status,
)
from fastapi.responses import ORJSONResponse

from app.api import dependencies, health_helpers
from app.domain.schemas import api as schemas
from app.services.service import BudgetService

router = APIRouter(tags=["Budget"])
settings_router = APIRouter(tags=["Budget Settings"])
dashboard_router = APIRouter(tags=["Budget Dashboard"])


@router.get("/health/live", status_code=status.HTTP_200_OK, summary="Liveness probe")
async def liveness_check() -> dict:
    return {"status": "ok"}


@router.get("/health", status_code=status.HTTP_200_OK, summary="Health check")
async def health_check() -> dict:
    return {"status": "Healthy"}


@router.get("/health/ready", status_code=status.HTTP_200_OK, summary="Readiness probe")
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
    "",
    response_model=schemas.BudgetResponse,
    summary="Получение бюджета",
)
async def get_budget(
    target_date: date | None = Query(None, alias="month"),
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: BudgetService = Depends(dependencies.get_budget_service),
):
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
    budget_id = await service.create_budget(user_id, request, target_date)
    return schemas.CreateBudgetResponse(budget_id=budget_id)


@settings_router.get(
    "/budget",
    response_model=schemas.BudgetSettingsResponse,
    summary="Получение настроек бюджета",
)
async def get_budget_settings(
    target_date: date | None = Query(None, alias="month"),
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: BudgetService = Depends(dependencies.get_budget_service),
):
    return await service.get_budget_settings(user_id, target_date)


@dashboard_router.get(
    "/budget",
    response_model=schemas.DashboardBudgetResponse,
    summary="Получение бюджета для главного экрана",
)
async def get_dashboard_budget(
    target_date: date | None = Query(None, alias="month"),
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: BudgetService = Depends(dependencies.get_budget_service),
):
    return await service.get_dashboard_budget(user_id, target_date)


@settings_router.patch(
    "/budget",
    status_code=status.HTTP_200_OK,
    summary="Обновление настроек бюджета",
)
async def patch_budget_settings(
    request: schemas.PatchBudgetRequest = Body(...),
    target_date: date | None = Query(None, alias="month"),
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: BudgetService = Depends(dependencies.get_budget_service),
):
    await service.patch_budget(user_id, request, target_date)
    return ORJSONResponse(content=None)
