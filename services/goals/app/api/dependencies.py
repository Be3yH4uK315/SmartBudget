from uuid import UUID

from fastapi import Depends, HTTPException, Query, Request, status

from app.domain.enums import GoalPriority
from app.infrastructure.db.uow import UnitOfWork
from app.services.service import GoalService


async def get_uow(request: Request) -> UnitOfWork:
    """Создает UnitOfWork с фабрикой сессий из app.state."""
    db_session_maker = getattr(request.app.state, "db_session_maker", None)
    if db_session_maker is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database session factory not available",
        )

    return UnitOfWork(db_session_maker)


def get_goal_service(uow: UnitOfWork = Depends(get_uow)) -> GoalService:
    """Создает сервис целей."""
    return GoalService(uow)


async def get_current_user_id(request: Request) -> UUID:
    """Извлекает user_id из X-User-Id, который устанавливает API Gateway."""
    user_id = request.headers.get("X-User-Id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID header missing",
        )

    try:
        return UUID(user_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid User ID format",
        ) from exc


class GoalFilters:
    """Query-фильтры для получения списка целей."""

    def __init__(
        self,
        limitAmount: int = Query(100, ge=1, le=1000, description="Лимит записей"),
        offset: int = Query(0, ge=0, description="Смещение"),
        tags: str | None = Query(
            None,
            description="Теги через запятую, например: Travel,Auto",
        ),
        priorities: str | None = Query(
            None,
            description="Приоритеты через запятую: High,Medium,Low",
        ),
        is_archived: bool = Query(False, description="Показывать архивные цели"),
    ) -> None:
        self.limitAmount = limitAmount
        self.offset = offset
        self.is_archived = is_archived
        self.tags_list = self._parse_tags(tags)
        self.priorities_list = self._parse_priorities(priorities)

    @staticmethod
    def _parse_tags(tags: str | None) -> list[str] | None:
        """Преобразует строку тегов в список."""
        if not tags:
            return None

        parsed_tags = [tag.strip() for tag in tags.split(",") if tag.strip()]
        return parsed_tags or None

    @staticmethod
    def _parse_priorities(priorities: str | None) -> list[GoalPriority] | None:
        """Преобразует строку приоритетов в список GoalPriority."""
        if not priorities:
            return None

        try:
            parsed_priorities = [
                GoalPriority(priority.strip())
                for priority in priorities.split(",")
                if priority.strip()
            ]
        except ValueError as exc:
            allowed_values = [priority.value for priority in GoalPriority]
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"Invalid priority value. Allowed: {allowed_values}",
            ) from exc

        return parsed_priorities or None
