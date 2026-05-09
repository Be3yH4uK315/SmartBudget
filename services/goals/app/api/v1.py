from fastapi import APIRouter

from app.api.routers import dashboard, goals, health

api_router = APIRouter()

api_router.include_router(health.router, prefix="/goals")
api_router.include_router(goals.router, prefix="/goals")
api_router.include_router(dashboard.router, prefix="/dashboard")