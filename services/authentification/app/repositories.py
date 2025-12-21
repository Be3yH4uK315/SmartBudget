from datetime import datetime, timezone
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import and_, delete, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas

class BaseRepository:
    """Базовый репозиторий. Не управляет транзакциями."""

    def __init__(self, db: AsyncSession):
        self.db = db

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
        """Получает только роль пользователя по ID."""
        result = await self.db.execute(
            select(models.User.role).where(models.User.user_id == user_id)
        )
        return result.scalar_one_or_none() or schemas.UserRole.USER.value

    def create(self, user: models.User) -> models.User:
        """Создает нового пользователя."""
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

class SessionRepository(BaseRepository):
    """Репозиторий для операций с сессиями."""

    def create(self, session: models.Session) -> models.Session:
        """Создает новую сессию."""
        self.db.add(session)
        return session

    async def get_by_fingerprint(self, fingerprint: str) -> models.Session | None:
        """Находит активную сессию по fingerprint."""
        query = select(models.Session).where(
            and_(
                models.Session.refresh_fingerprint == fingerprint,
                models.Session.revoked == sa.false(),
                models.Session.expires_at > datetime.now(timezone.utc),
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_fingerprint(
        self, 
        session: models.Session, 
        new_fingerprint: str,
        new_expires_at: datetime
    ) -> None:
        """Обновляет fingerprint и срок действия (при refresh)."""
        session.refresh_fingerprint = new_fingerprint
        session.expires_at = new_expires_at
        self.db.add(session)

    async def revoke_by_fingerprint(self, user_id: UUID, fingerprint: str) -> None:
        """Отзывает сессию по fingerprint."""
        await self.db.execute(
            update(models.Session)
            .where(
                and_(
                    models.Session.user_id == user_id,
                    models.Session.refresh_fingerprint == fingerprint,
                )
            )
            .values(revoked=True)
        )

    async def get_all_active(self, user_id: UUID) -> list[models.Session]:
        """Получает все активные сессии пользователя."""
        query = (
            select(models.Session)
            .where(
                and_(
                    models.Session.user_id == user_id,
                    models.Session.revoked == sa.false(),
                )
            )
            .order_by(models.Session.created_at.desc())
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def revoke_by_id(self, user_id: UUID, session_id: UUID) -> None:
        """Отзывает конкретную сессию по ее ID."""
        await self.db.execute(
            update(models.Session)
            .where(
                and_(
                    models.Session.session_id == session_id,
                    models.Session.user_id == user_id,
                )
            )
            .values(revoked=True)
        )

    async def revoke_all_except(self, user_id: UUID, current_fingerprint: str) -> int:
        """Отзывает все сессии, кроме текущей."""
        result = await self.db.execute(
            update(models.Session)
            .where(
                and_(
                    models.Session.user_id == user_id,
                    models.Session.refresh_fingerprint != current_fingerprint,
                    models.Session.revoked == sa.false(),
                )
            )
            .values(revoked=True)
        )
        return result.rowcount or 0

    async def revoke_all_for_user(self, user_id: UUID) -> None:
        """Отзывает все сессии пользователя."""
        await self.db.execute(
            update(models.Session)
            .where(models.Session.user_id == user_id)
            .values(revoked=True)
        )

    async def delete_expired_or_revoked(self) -> int:
        """Удаляет сессии, которые истекли по времени или были отозваны."""
        result = await self.db.execute(
            delete(models.Session).where(
                or_(
                    models.Session.expires_at < datetime.now(timezone.utc),
                    models.Session.revoked == sa.true()
                )
            )
        )
        return result.rowcount