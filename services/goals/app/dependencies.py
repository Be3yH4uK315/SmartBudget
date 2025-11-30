from fastapi import Depends, Path, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from typing import AsyncGenerator
from uuid import UUID
from arq.connections import ArqRedis

from app import settings, repositories, services
from app.kafka_producer import KafkaProducer, kafka_producer

def get_async_engine():
    return create_async_engine(settings.settings.db.db_url)

def get_async_session_maker():
    engine = get_async_engine()
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    session_maker = get_async_session_maker()
    async with session_maker() as session:
        yield session

def get_goal_repository(db: AsyncSession = Depends(get_db)) -> repositories.GoalRepository:
    """Провайдер для GoalRepository."""
    return repositories.GoalRepository(db)

async def get_kafka_producer() -> KafkaProducer:
    """Зависимость для Kafka-продюсера (из lifespan)."""
    return kafka_producer

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