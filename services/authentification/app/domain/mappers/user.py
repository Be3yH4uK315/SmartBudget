from app.infrastructure.db import models
from app.domain.schemas.dtos import UserDTO
from app.domain.schemas.api import UserRole


def user_to_dto(user: models.User) -> UserDTO:
    """Безопасный mapper ORM → DTO."""
    return UserDTO(
        user_id=user.user_id,
        email=user.email,
        name=user.name,
        country=user.country,
        role=UserRole(user.role),
        is_active=user.is_active,
        last_login=user.last_login,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )