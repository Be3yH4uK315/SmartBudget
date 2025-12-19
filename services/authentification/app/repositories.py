from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_, select, update, delete, and_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import sqlalchemy as sa
from uuid import UUID
from datetime import datetime, timezone
import logging

from app import models, exceptions

logger = logging.getLogger(__name__)

class BaseRepository:
    """Базовый репозиторий для внедрения сессии БД."""
    def __init__(self, db: AsyncSession):
        self.db = db

class UserRepository(BaseRepository):
    """Репозиторий для операций с пользователями."""

    async def get_by_email(self, email: str) -> models.User | None:
        """Получает пользователя по email."""
        try:
            result = await self.db.execute(
                select(models.User).where(models.User.email == email.lower().strip())
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Database error getting user by email: {e}")
            raise exceptions.DatabaseError("Failed to get user")

    async def get_by_id(self, user_id: UUID) -> models.User | None:
        """Получает пользователя по ID."""
        try:
            return await self.db.get(models.User, user_id)
        except SQLAlchemyError as e:
            logger.error(f"Database error getting user by ID: {e}")
            raise exceptions.DatabaseError("Failed to get user")

    async def get_role_by_id(self, user_id: UUID) -> int:
        """Получает только роль пользователя по ID."""
        try:
            result = await self.db.execute(
                select(models.User.role).where(models.User.user_id == user_id)
            )
            role = result.scalar()
            return role or models.UserRole.USER
        except SQLAlchemyError as e:
            logger.error(f"Database error getting user role: {e}")
            raise exceptions.DatabaseError("Failed to get user role")

    async def create(self, user_model: models.User) -> models.User:
        """Создает нового пользователя."""
        try:
            self.db.add(user_model)
            await self.db.commit()
            await self.db.refresh(user_model)
            logger.info(f"User created: {user_model.user_id}")
            return user_model
        except IntegrityError as e:
            await self.db.rollback()
            logger.warning(f"User creation failed - email exists: {user_model.email}")
            raise exceptions.EmailAlreadyExistsError("Email already registered")
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Database error creating user: {e}")
            raise exceptions.DatabaseError("Failed to create user")

    async def update_last_login(self, user_id: UUID) -> None:
        """Обновляет время последнего входа."""
        try:
            await self.db.execute(
                update(models.User)
                .where(models.User.user_id == user_id)
                .values(last_login=datetime.now(timezone.utc))
            )
            await self.db.commit()
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Error updating last login: {e}")

    async def update_password(self, user: models.User, new_hash: str) -> None:
        """Обновляет хэш пароля."""
        try:
            user.password_hash = new_hash
            user.updated_at = datetime.now(timezone.utc)
            self.db.add(user)
            await self.db.commit()
            logger.info(f"Password updated for user: {user.user_id}")
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Error updating password: {e}")
            raise exceptions.DatabaseError("Failed to update password")

class SessionRepository(BaseRepository):
    """Репозиторий для операций с сессиями."""

    async def create(self, session: models.Session) -> models.Session:
        """Создает новую сессию."""
        try:
            self.db.add(session)
            await self.db.commit()
            await self.db.refresh(session)
            logger.debug(f"Session created: {session.session_id}")
            return session
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Error creating session: {e}")
            raise exceptions.DatabaseError("Failed to create session")

    async def get_by_fingerprint(self, fingerprint: str) -> models.Session | None:
        """Находит активную сессию по fingerprint."""
        try:
            query = select(models.Session).where(
                and_(
                    models.Session.refresh_fingerprint == fingerprint,
                    models.Session.revoked == sa.false(),
                    models.Session.expires_at > datetime.now(timezone.utc)
                )
            )
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Error getting session by fingerprint: {e}")
            raise exceptions.DatabaseError("Failed to get session")

    async def update_fingerprint(
        self, 
        session: models.Session, 
        new_fingerprint: str,
        new_expires_at: datetime
    ) -> None:
        """Обновляет fingerprint и срок действия (при refresh)."""
        try:
            session.refresh_fingerprint = new_fingerprint
            session.expires_at = new_expires_at
            self.db.add(session)
            await self.db.commit()
            logger.debug(f"Session fingerprint updated: {session.session_id}")
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Error updating session fingerprint: {e}")
            raise exceptions.DatabaseError("Failed to update session")

    async def revoke_by_fingerprint(self, user_id: UUID, fingerprint: str) -> None:
        """Отзывает сессию по fingerprint."""
        try:
            await self.db.execute(
                update(models.Session).where(
                    and_(
                        models.Session.user_id == user_id,
                        models.Session.refresh_fingerprint == fingerprint
                    )
                ).values(revoked=True)
            )
            await self.db.commit()
            logger.debug(f"Session revoked for user: {user_id}")
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Error revoking session: {e}")

    async def get_all_active(self, user_id: UUID) -> list[models.Session]:
        """Получает все активные сессии пользователя."""
        try:
            query = (
                select(models.Session)
                .where(
                    and_(
                        models.Session.user_id == user_id,
                        models.Session.revoked == sa.false()
                    )
                )
                .order_by(models.Session.created_at.desc())
            )
            result = await self.db.execute(query)
            return result.scalars().all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting active sessions: {e}")
            return []

    async def revoke_by_id(self, user_id: UUID, session_id: UUID) -> None:
        """Отзывает конкретную сессию по ее ID."""
        try:
            query = (
                update(models.Session)
                .where(
                    and_(
                        models.Session.session_id == session_id,
                        models.Session.user_id == user_id
                    )
                )
                .values(revoked=True)
            )
            await self.db.execute(query)
            await self.db.commit()
            logger.info(f"Session revoked: {session_id}")
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Error revoking session by ID: {e}")

    async def revoke_all_except(self, user_id: UUID, current_fingerprint: str) -> int:
        """Отзывает все сессии, кроме текущей."""
        try:
            query = (
                update(models.Session)
                .where(
                    and_(
                        models.Session.user_id == user_id,
                        models.Session.refresh_fingerprint != current_fingerprint,
                        models.Session.revoked == sa.false()
                    )
                )
                .values(revoked=True)
            )
            result = await self.db.execute(query)
            await self.db.commit()
            count = result.rowcount
            logger.info(f"Revoked {count} sessions for user: {user_id}")
            return count
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Error revoking all except: {e}")
            return 0

    async def revoke_all_for_user(self, user_id: UUID) -> None:
        """Отзывает все сессии пользователя."""
        try:
            await self.db.execute(
                update(models.Session)
                .where(models.Session.user_id == user_id)
                .values(revoked=True)
            )
            await self.db.commit()
            logger.info(f"All sessions revoked for user: {user_id}")
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Error revoking all sessions: {e}")

    async def cleanup_expired(self) -> int:
        """Удаляет истекшие и отозванные сессии."""
        try:
            result = await self.db.execute(
                delete(models.Session).where(
                    or_(
                        models.Session.expires_at < datetime.now(timezone.utc),
                        models.Session.revoked == sa.true()
                    )
                )
            )
            await self.db.commit()
            count = result.rowcount
            logger.info(f"Cleaned up {count} expired/revoked sessions")
            return count
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Error cleaning up sessions: {e}")
            return 0