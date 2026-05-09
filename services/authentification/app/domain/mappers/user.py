from app.domain.schemas.api import Gender, Language, UserRole
from app.domain.schemas.dtos import UserDTO
from app.infrastructure.db import models


def user_to_dto(user: models.User) -> UserDTO:
    """Преобразует ORM-модель пользователя во внутренний DTO."""
    return UserDTO(
        user_id=user.user_id,
        email=user.email,
        name=user.name,
        language=Language(user.language),
        role=UserRole(user.role),
        gender=Gender(user.gender) if user.gender else None,
        is_active=user.is_active,
        last_login=user.last_login,
        retention_days=user.retention_days,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )
