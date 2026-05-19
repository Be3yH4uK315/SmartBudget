from uuid import UUID

from arq import ArqRedis
from fastapi import Depends, HTTPException, Query, Request, status

from app.domain.enums import (
    NotificationServiceType,
    NotificationStatus,
    NotificationType,
)
from app.infrastructure.db.uow import UnitOfWork
from app.services.service import NotificationService

FILTERABLE_NOTIFICATION_SERVICES = {
    NotificationServiceType.LIMIT,
    NotificationServiceType.BUDGET,
    NotificationServiceType.GOALS,
    NotificationServiceType.TRANSACTIONS,
    NotificationServiceType.SECURITY,
}


async def get_uow(request: Request) -> UnitOfWork:
    """Создает UnitOfWork с фабрикой сессий из app.state."""
    db_session_maker = getattr(request.app.state, "db_session_maker", None)
    if db_session_maker is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database session factory not available",
        )

    return UnitOfWork(db_session_maker)


def get_arq_pool(request: Request) -> ArqRedis | None:
    """Возвращает ARQ pool для постановки фоновых задач."""
    return getattr(request.app.state, "arq_pool", None)


def get_notification_service(
    uow: UnitOfWork = Depends(get_uow),
    arq_pool: ArqRedis | None = Depends(get_arq_pool),
) -> NotificationService:
    """Создает сервис уведомлений."""
    return NotificationService(
        unit_of_work=uow,
        arq_pool=arq_pool,
    )


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


async def get_current_session_id(request: Request) -> UUID | None:
    """Извлекает session_id из X-Session-Id, который устанавливает API Gateway."""
    session_id = request.headers.get("X-Session-Id")
    if not session_id:
        return None

    try:
        return UUID(session_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Session ID format",
        ) from exc


class NotificationFilters:
    """Query-фильтры для получения списка уведомлений."""

    def __init__(
        self,
        services: str | None = Query(
            None,
            description="Сервисы через запятую: Limit,Budget,Goals,Transactions,Security",
        ),
        types: str | None = Query(
            None,
            description="Типы через запятую: info,success,alert,warning,system",
        ),
        statuses: str | None = Query(
            None,
            description="Статусы через запятую: unread,read",
        ),
        limit: int = Query(20, ge=1, le=100, description="Лимит записей"),
        offset: int = Query(0, ge=0, description="Смещение"),
    ) -> None:
        self.limit = limit
        self.offset = offset
        self.services = self._parse_services(services)
        self.types = self._parse_enum_values(types, NotificationType, "types")
        self.statuses = self._parse_enum_values(statuses, NotificationStatus, "statuses")

    @staticmethod
    def _split_values(raw: str | None) -> list[str]:
        """Преобразует query-параметр в список значений."""
        if not raw:
            return []

        return [item.strip() for item in raw.split(",") if item.strip()]

    @classmethod
    def _parse_services(
        cls,
        raw: str | None,
    ) -> list[NotificationServiceType] | None:
        """Парсит список сервисов уведомлений."""
        values = cls._split_values(raw)
        if not values:
            return None

        parsed: list[NotificationServiceType] = []
        for value in values:
            try:
                service_type = NotificationServiceType(value)
            except ValueError as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid services filter value: {value}",
                ) from exc

            if service_type not in FILTERABLE_NOTIFICATION_SERVICES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid services filter value: {value}",
                )

            parsed.append(service_type)

        return parsed

    @classmethod
    def _parse_enum_values(
        cls,
        raw: str | None,
        enum_type: type[NotificationType] | type[NotificationStatus],
        field_name: str,
    ) -> list[NotificationType] | list[NotificationStatus] | None:
        """Парсит список enum-значений из CSV query-параметра."""
        values = cls._split_values(raw)
        if not values:
            return None

        parsed = []
        for value in values:
            try:
                parsed.append(enum_type(value))
            except ValueError as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid {field_name} filter value: {value}",
                ) from exc

        return parsed
