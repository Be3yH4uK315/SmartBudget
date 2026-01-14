import asyncio
import logging
from datetime import datetime, timezone, timedelta
from time import monotonic
from uuid import UUID

from redis.asyncio import Redis

from app.core import exceptions, config
from app.infrastructure.db import uow
from app.domain.schemas import api as api_schemas
from app.domain.schemas.dtos import UserDTO, SessionDTO
from app.domain.mappers.user import user_to_dto
from app.domain.mappers.session import session_to_dto
from app.services.session_service import SessionService
from app.services.notifier import AuthNotifier
from app.utils import crypto


logger = logging.getLogger(__name__)
settings = config.settings


class LoginService:
    """Сервис аутентификации."""

    def __init__(
        self,
        uow: uow.UnitOfWork,
        redis: Redis,
        session_service: SessionService,
        notifier: AuthNotifier,
    ):
        self.uow = uow
        self.redis = redis
        self.session_service = session_service
        self.notifier = notifier

    async def authenticate_user(
        self,
        body: api_schemas.LoginRequest,
        ip: str,
        user_agent: str | None,
    ) -> tuple[UserDTO, SessionDTO, str, str]:
        location = "Unknown"

        async with self.uow:
            user_orm = await self.uow.users.get_by_email(body.email)

            if (
                user_orm
                and user_orm.is_locked
                and user_orm.locked_until
                and user_orm.locked_until > datetime.now(timezone.utc)
            ):
                logger.warning(
                    "Login locked",
                    extra={"email": body.email},
                )
                raise exceptions.InvalidCredentialsError(
                    "Account is temporarily locked"
                )

            if user_orm and user_orm.is_locked:
                user_orm.is_locked = False
                user_orm.locked_until = None

            password_hash = (
                user_orm.password_hash
                if user_orm
                else settings.APP.DUMMY_HASH
            )
            user_id_str = (
                str(user_orm.user_id) if user_orm else None
            )

        start = monotonic()
        password_valid = await crypto.check_password(
            body.password,
            password_hash,
        )
        elapsed = monotonic() - start

        if elapsed < 0.08:
            await asyncio.sleep(0.08 - elapsed)

        if (
            not user_orm
            or not password_valid
            or not user_orm.is_active
        ):
            if user_id_str:
                attempts_key = (
                    f"auth:login_attempts:{user_id_str}"
                )
                failed_attempts = await self.redis.incr(
                    attempts_key
                )
                await self.redis.expire(
                    attempts_key,
                    1800,
                )

                if failed_attempts >= 5:
                    async with self.uow:
                        user_for_lock = (
                            await self.uow.users.get_by_id(
                                UUID(user_id_str)
                            )
                        )
                        if user_for_lock:
                            user_for_lock.is_locked = True
                            user_for_lock.locked_until = (
                                datetime.now(timezone.utc)
                                + timedelta(minutes=30)
                            )
                        await self.uow.commit()

                    logger.warning(
                        "User locked due to failed attempts",
                        extra={"user_id": user_id_str},
                    )

            await self.notifier.notify_login_failed(
                body.email,
                ip,
                location,
            )
            raise exceptions.InvalidCredentialsError(
                "Invalid credentials"
            )
        
        if user_id_str:
            await self.redis.delete(
                f"auth:login_attempts:{user_id_str}"
            )

        async with self.uow:
            user_active = await self.uow.users.get_by_id(
                UUID(user_id_str)
            )

            await self.uow.users.update_last_login(
                user_active.user_id
            )

            access_token, refresh_token, session_orm = (
                await self.session_service.create_session_and_tokens(
                    user=user_active,
                    user_agent=user_agent or "Unknown",
                    device_name="Detecting...",
                    ip=ip,
                    location=location,
                )
            )

            user_dto = user_to_dto(user_active)
            session_dto = session_to_dto(session_orm)
            session_dto.is_current = True

            await self.notifier.notify_login(
                user_dto,
                ip,
                location,
            )

            await self.uow.commit()

        await self.session_service.activate_session_in_cache(
            session_dto,
            user_dto,
        )

        await self.notifier.enrich_session(
            session_id=session_dto.session_id,
            ip=ip,
            user_agent=user_agent or "Unknown",
        )

        return (
            user_dto,
            session_dto,
            access_token,
            refresh_token,
        )

    async def logout(
        self,
        user_id: str,
        refresh_token: str,
    ) -> None:
        fingerprint = crypto.hash_token(refresh_token)
        session_id: UUID | None = None

        async with self.uow:
            session = await self.uow.sessions.get_by_fingerprint(
                fingerprint
            )
            if session:
                session_id = session.session_id
                await self.uow.sessions.revoke_by_id(
                    UUID(user_id),
                    session.session_id,
                )

            await self.notifier.notify_logout(user_id)
            await self.uow.commit()

        if session_id:
            await self.session_service.clear_session_cache(
                session_id
            )