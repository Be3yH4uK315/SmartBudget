from fastapi import APIRouter

from app.api.routers import goals, health, transactions

api_router = APIRouter()

api_router.include_router(health.router, prefix="/transactions")
api_router.include_router(transactions.router, prefix="/transactions")
api_router.include_router(goals.router, prefix="/goals")