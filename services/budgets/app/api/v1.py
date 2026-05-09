from fastapi import APIRouter

from app.api.routers import budgets, dashboard, health, settings

api_router = APIRouter()

api_router.include_router(health.router, prefix="/budget")
api_router.include_router(budgets.router, prefix="/budget")
api_router.include_router(settings.router, prefix="/settings")
api_router.include_router(dashboard.router, prefix="/dashboard")