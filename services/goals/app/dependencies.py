from fastapi import Depends, Path, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator
from uuid import UUID
from arq.connections import ArqRedis

from app import (
    repositories, 
    services
)
from app.kafka_producer import KafkaProducer

async def get_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """Получает session_maker из app.state и предоставляет сессию."""
    session_maker = request.app.state.async_session_maker
    if not session_maker:
        raise HTTPException(status_code=500, detail="Database session factory not available")
        
    async with session_maker() as session:
        yield session

def get_goal_repository(db: AsyncSession = Depends(get_db)) -> repositories.GoalRepository:
    """Провайдер для GoalRepository."""
    return repositories.GoalRepository(db)

async def get_kafka_producer(request: Request) -> KafkaProducer:
    """Получает kafka_producer из app.state."""
    kafka_prod = request.app.state.kafka_producer
    if not kafka_prod:
        raise HTTPException(status_code=500, detail="Kafka producer not available")
    return kafka_prod

async def get_arq_pool(request: Request) -> AsyncGenerator[ArqRedis, None]:
    """Предоставляет пул Arq из app.state."""
    arq_pool: ArqRedis = request.app.state.arq_pool
    try:
        yield arq_pool
    finally:
        pass

def get_goal_service(
    repo: repositories.GoalRepository = Depends(get_goal_repository),
    kafka: KafkaProducer = Depends(get_kafka_producer)
) -> services.GoalService:
    """Провайдер для GoalService."""
    return services.GoalService(repo, kafka)

def get_user_id(
    user_id: UUID = Path(..., description="ID пользователя (UUID)")
) -> UUID:
    """
    Извлекает user_id из пути.
    (Предполагается, что API Gateway уже проверил токен)
    """
    return user_id