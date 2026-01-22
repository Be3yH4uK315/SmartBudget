from typing import Optional
from fastapi import Depends, Query, status, HTTPException, Request
from uuid import UUID

from app.domain.enums import GoalPriority
from app.infrastructure.db.uow import UnitOfWork
from app.services.service import GoalService

async def get_uow(request: Request) -> UnitOfWork:
    """Создает UnitOfWork с фабрикой сессий из app.state."""
    db_session_maker = request.app.state.db_session_maker
    if not db_session_maker:
        raise HTTPException(status_code=500, detail="Database session factory not available")
    
    return UnitOfWork(db_session_maker)

def get_goal_service(uow: UnitOfWork = Depends(get_uow)) -> GoalService:
    """Создает сервис целей."""
    return GoalService(uow)

async def get_current_user_id(request: Request) -> UUID:
    """Извлекает user_id из заголовка X-User-Id, который устанавливает API Gateway."""
    user_id = request.headers.get("X-User-Id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID header missing"
        )
    try:
        return UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid User ID format"
        )

class GoalFilters:
    """
    Зависимость для парсинга фильтров целей из Query параметров.
    Превращает "tag1,tag2" -> ["tag1", "tag2"].
    """
    def __init__(
        self,
        limit: int = Query(100, ge=1, le=1000, description="Лимит записей"),
        offset: int = Query(0, ge=0, description="Смещение"),
        tags: Optional[str] = Query(None, description="Теги через запятую (напр. 'Travel,Auto')"),
        priorities: Optional[str] = Query(None, description="Приоритеты через запятую (напр. 'high,medium')"),
        is_archived: bool = Query(False, description="Показывать архивные"),
    ):
        self.limit = limit
        self.offset = offset
        self.is_archived = is_archived
        
        self.tags_list: Optional[list[str]] = None
        if tags:
            self.tags_list = [t.strip() for t in tags.split(",") if t.strip()]

        self.priorities_list: Optional[list[GoalPriority]] = None
        if priorities:
            try:
                self.priorities_list = [
                    GoalPriority(p.strip()) 
                    for p in priorities.split(",") 
                    if p.strip()
                ]
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail=f"Invalid priority value. Allowed: {[e.value for e in GoalPriority]}"
                )