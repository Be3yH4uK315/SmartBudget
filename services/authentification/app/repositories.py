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

    async def getByEmail(self, email: str) -> models.User | None:
        """Получает пользователя по email."""
        result = await self.db.execute(
            select(models.User).where(models.User.email == email)
        )
        return result.scalar_one_or_none()

    async def getById(self, userId: UUID) -> models.User | None:
        """Получает пользователя по ID."""
        return await self.db.get(models.User, userId)

    async def getRoleById(self, userId: UUID) -> int:
        """Получает только роль пользователя по ID."""
        result = await self.db.execute(
            select(models.User.role).where(models.User.userId == userId)
        )
        return result.scalar() or models.UserRole.USER.value

    async def create(self, userModel: models.User) -> models.User:
        """Создает нового пользователя."""
        try:
            self.db.add(userModel)
            await self.db.commit()
            await self.db.refresh(userModel)
            return userModel
        except IntegrityError:
            await self.db.rollback()
            middleware.logger.warning(f"Registration attempt for existing email: {userModel.email}")
            raise exceptions.EmailAlreadyExistsError("Email already registered")

    async def updateLastLogin(self, userId: UUID):
        """Обновляет время последнего входа пользователя."""
        await self.db.execute(
            update(models.User)
            .where(models.User.userId == userId)
            .values(lastLogin=datetime.now(timezone.utc))
        )
        await self.db.commit()

    async def updatePassword(self, user: models.User, newHash: str):
        """Обновляет хэш пароля пользователя."""
        user.passwordHash = newHash
        self.db.add(user)
        await self.db.commit()

class SessionRepository(BaseRepository):
    """Репозиторий для операций с сессиями."""

    async def create(self, session: models.Session) -> models.Session:
        """Создает новую сессию."""
        self.db.add(session)
        await self.db.commit()
        return session

    async def getByFingerprint(self, fingerprint: str) -> models.Session | None:
        """Находит активную сессию по fingerprint."""
        query = select(models.Session).where(
            models.Session.refreshFingerprint == fingerprint,
            models.Session.revoked == sa.false(),
            models.Session.expiresAt > datetime.now(timezone.utc)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def updateFingerprint(
        self, 
        session: models.Session, 
        newFingerprint: str,
        newExpiresAt: datetime
    ):
        """Обновляет fingerprint и срок действия сессии (при refresh)."""
        session.refreshFingerprint = newFingerprint
        session.expiresAt = newExpiresAt
        await self.db.commit()

    async def revokeByFingerprint(self, userId: UUID, fingerprint: str):
        """Отзывает сессию по fingerprint (при logout)."""
        await self.db.execute(
            update(models.Session).where(
                models.Session.userId == userId,
                models.Session.refreshFingerprint == fingerprint
            ).values(revoked=True)
        )
        await self.db.commit()

    async def getAllActive(self, userId: UUID) -> list[models.Session]:
        """Получает все активные (не отозванные) сессии пользователя."""
        query = (
            select(models.Session)
            .where(
                models.Session.userId == userId,
                models.Session.revoked == sa.false()
            )
            .order_by(models.Session.createdAt.desc())
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def revokeById(self, userId: UUID, sessionId: UUID):
        """Отзывает конкретную сессию по ее ID."""
        query = (
            update(models.Session)
            .where(
                models.Session.sessionId == sessionId,
                models.Session.userId == userId
            )
            .values(revoked=True)
        )
        await self.db.execute(query)
        await self.db.commit()

    async def revokeAllExcept(self, userId: UUID, currentFingerprint: str) -> int:
        """Отзывает все сессии, кроме текущей."""
        query = (
            update(models.Session)
            .where(
                models.Session.userId == userId,
                models.Session.refreshFingerprint != currentFingerprint,
                models.Session.revoked == sa.false()
            )
            .values(revoked=True)
        )
        result = await self.db.execute(query)
        await self.db.commit()
        return result.rowcount

    async def revokeAllForUser(self, userId: UUID):
        """Отзывает абсолютно все сессии пользователя (при сбросе пароля)."""
        await self.db.execute(
            update(models.Session)
            .where(models.Session.userId == userId)
            .values(revoked=True)
        )
        await self.db.commit()