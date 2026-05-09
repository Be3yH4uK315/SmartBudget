from fastapi import APIRouter

from app.api.routers import auth, gateway, health, jwks, profile, sessions, settings

api_router = APIRouter()

api_router.include_router(health.router, prefix="/auth")
api_router.include_router(auth.router, prefix="/auth")
api_router.include_router(jwks.router, prefix="/auth")
api_router.include_router(gateway.router, prefix="/auth")

api_router.include_router(profile.router, prefix="/user")

api_router.include_router(settings.router, prefix="/settings")
api_router.include_router(sessions.router, prefix="/settings")
