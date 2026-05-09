from fastapi import APIRouter

from app.api.routers import health, notifications, push, settings, websockets

api_router = APIRouter()

api_router.include_router(health.router, prefix="/notifications")
api_router.include_router(notifications.router, prefix="/notifications")
api_router.include_router(websockets.router, prefix="/notifications")

api_router.include_router(settings.router, prefix="/settings/notifications")
api_router.include_router(push.router, prefix="/push")