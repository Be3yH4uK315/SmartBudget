from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy import select, update
from app.infrastructure.db import models
from app.domain.schemas import api as schemas
from app.infrastructure.db.repositories.base import BaseRepository

class UserRepository(BaseRepository):
    """Репозиторий для операций с пользователями."""

    async def get_by_email(self, email: str) -> models.User | None:
        """Получает пользователя по email."""
        result = await self.db.execute(
            select(models.User).where(models.User.email == email.lower().strip())
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: UUID) -> models.User | None:
        """Получает пользователя по ID."""
        return await self.db.get(models.User, user_id)

    async def get_role_by_id(self, user_id: UUID) -> int:
        """Получает только роль пользователя по ID (оптимизация)."""
        result = await self.db.execute(
            select(models.User.role).where(models.User.user_id == user_id)
        )
        val = result.scalar_one_or_none()
        return val if val is not None else schemas.UserRole.USER.value

    def create(self, user: models.User) -> models.User:
        """Создает нового пользователя (не делает commit)."""
        self.db.add(user)
        return user

    async def update_last_login(self, user_id: UUID) -> None:
        """Обновляет время последнего входа."""
        await self.db.execute(
            update(models.User)
            .where(models.User.user_id == user_id)
            .values(last_login=datetime.now(timezone.utc))
        )

    def update_password(self, user: models.User, new_hash: str) -> None:
        """Обновляет хэш пароля."""
        user.password_hash = new_hash
        user.updated_at = datetime.now(timezone.utc)
        self.db.add(user)
