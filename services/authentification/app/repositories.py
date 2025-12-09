from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
import sqlalchemy as sa
from uuid import UUID
from datetime import datetime, timezone

from app import (
    models, 
    exceptions, 
    middleware
)

class BaseRepository:
    """Базовый репозиторий для внедрения сессии БД."""
    def __init__(self, db: AsyncSession):
        self.db = db

class UserRepository(BaseRepository):
    """Репозиторий для операций с пользователями."""

    async def get_by_email(self, email: str) -> models.User | None:
        """Получает пользователя по email."""
        result = await self.db.execute(
            select(models.User).where(models.User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: UUID) -> models.User | None:
        """Получает пользователя по ID."""
        return await self.db.get(models.User, user_id)

    async def get_role_by_id(self, user_id: UUID) -> int:
        """Получает только роль пользователя по ID."""
        result = await self.db.execute(
            select(models.User.role).where(models.User.id == user_id)
        )
        return result.scalar() or models.UserRole.USER.value

    async def create(self, user_model: models.User) -> models.User:
        """Создает нового пользователя."""
        try:
            self.db.add(user_model)
            await self.db.commit()
            await self.db.refresh(user_model)
            return user_model
        except IntegrityError:
            await self.db.rollback()
            middleware.logger.warning(f"Registration attempt for existing email: {user_model.email}")
            raise exceptions.EmailAlreadyExistsError("Email already registered")

    async def update_last_login(self, user_id: UUID):
        """Обновляет время последнего входа пользователя."""
        await self.db.execute(
            update(models.User)
            .where(models.User.id == user_id)
            .values(last_login=datetime.now(timezone.utc))
        )
        await self.db.commit()

    async def update_password(self, user: models.User, new_hash: str):
        """Обновляет хэш пароля пользователя."""
        user.password_hash = new_hash
        self.db.add(user)
        await self.db.commit()

class SessionRepository(BaseRepository):
    """Репозиторий для операций с сессиями."""

    async def create(self, session: models.Session) -> models.Session:
        """Создает новую сессию."""
        self.db.add(session)
        await self.db.commit()
        return session

    async def get_by_fingerprint(self, fingerprint: str) -> models.Session | None:
        """Находит активную сессию по fingerprint."""
        query = select(models.Session).where(
            models.Session.refresh_fingerprint == fingerprint,
            models.Session.revoked == sa.false(),
            models.Session.expires_at > datetime.now(timezone.utc)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_fingerprint(
        self, 
        session: models.Session, 
        new_fingerprint: str,
        new_expires_at: datetime
    ):
        """Обновляет fingerprint и срок действия сессии (при refresh)."""
        session.refresh_fingerprint = new_fingerprint
        session.expires_at = new_expires_at
        await self.db.commit()

    async def revoke_by_fingerprint(self, user_id: UUID, fingerprint: str):
        """Отзывает сессию по fingerprint (при logout)."""
        await self.db.execute(
            update(models.Session).where(
                models.Session.user_id == user_id,
                models.Session.refresh_fingerprint == fingerprint
            ).values(revoked=True)
        )
        await self.db.commit()

    async def get_all_active(self, user_id: UUID) -> list[models.Session]:
        """Получает все активные (не отозванные) сессии пользователя."""
        query = (
            select(models.Session)
            .where(
                models.Session.user_id == user_id,
                models.Session.revoked == sa.false()
            )
            .order_by(models.Session.created_at.desc())
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def revoke_by_id(self, user_id: UUID, session_id: UUID):
        """Отзывает конкретную сессию по ее ID."""
        query = (
            update(models.Session)
            .where(
                models.Session.id == session_id,
                models.Session.user_id == user_id
            )
            .values(revoked=True)
        )
        await self.db.execute(query)
        await self.db.commit()

    async def revoke_all_except(self, user_id: UUID, current_fingerprint: str) -> int:
        """Отзывает все сессии, кроме текущей."""
        query = (
            update(models.Session)
            .where(
                models.Session.user_id == user_id,
                models.Session.refresh_fingerprint != current_fingerprint,
                models.Session.revoked == sa.false()
            )
            .values(revoked=True)
        )
        result = await self.db.execute(query)
        await self.db.commit()
        return result.rowcount

    async def revoke_all_for_user(self, user_id: UUID):
        """Отзывает абсолютно все сессии пользователя (при сбросе пароля)."""
        await self.db.execute(
            update(models.Session)
            .where(models.Session.user_id == user_id)
            .values(revoked=True)
        )
        await self.db.commit()