import asyncio
import logging
from datetime import timedelta
from time import monotonic
from uuid import UUID

from redis.asyncio import Redis

from app.core import config, exceptions
from app.domain.mappers.session import session_to_dto
from app.domain.mappers.user import user_to_dto
from app.domain.schemas import api as api_schemas
from app.domain.schemas.dtos import SessionDTO, UserDTO
from app.infrastructure.db import uow
from app.services.notifier import AuthNotifier
from app.services.session_service import SessionService
from app.utils import crypto, time

logger = logging.getLogger(__name__)
settings = config.settings

MIN_PASSWORD_CHECK_SECONDS = 0.08
FAILED_LOGIN_TTL_SECONDS = 1800
FAILED_LOGIN_LIMIT = 5
ACCOUNT_LOCK_MINUTES = 30


class LoginService:
    """Сервис аутентификации пользователей."""

    def __init__(
        self,
        uow: uow.UnitOfWork,
        redis: Redis,
        session_service: SessionService,
        notifier: AuthNotifier,
    ) -> None:
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
        """Аутентифицирует пользователя и создает новую сессию."""
        normalized_email = body.email.lower().strip()
        resolved_user_agent = user_agent or "Unknown"
        location = "Unknown"

        async with self.uow:
            user = await self.uow.users.get_by_email(normalized_email)

            if _is_user_temporarily_locked(user):
                logger.warning(
                    "Login blocked: account is locked",
                    extra={"email": normalized_email},
                )
                raise exceptions.InvalidCredentialsError(
                    "Account is temporarily locked",
                )

            if user and user.is_locked:
                user.is_locked = False
                user.locked_until = None

            password_hash = user.password_hash if user else settings.APP.DUMMY_HASH
            user_id = user.user_id if user else None

            await self.uow.commit()

        password_valid = await self._check_password_with_min_delay(
            body.password,
            password_hash,
        )

        if not user or not password_valid or not user.is_active:
            if user_id:
                await self._register_failed_attempt(user_id)

            async with self.uow:
                await self.notifier.notify_login_failed(
                    normalized_email,
                    ip,
                    location,
                )
                await self.uow.commit()

            raise exceptions.InvalidCredentialsError("Invalid credentials")

        await self.redis.delete(_get_login_attempts_key(user.user_id))

        async with self.uow:
            active_user = await self.uow.users.get_by_id(user.user_id)
            if not active_user:
                raise exceptions.UserNotFoundError("User not found")

            await self.uow.users.update_last_login(active_user.user_id)

            (
                access_token,
                refresh_token,
                session,
            ) = await self.session_service.create_session_and_tokens(
                user=active_user,
                user_agent=resolved_user_agent,
                device_name="Detecting...",
                ip=ip,
                location=location,
            )

            user_dto = user_to_dto(active_user)
            session_dto = session_to_dto(session)
            session_dto.is_current = True

            await self.notifier.notify_login(
                user_dto,
                ip,
                location,
                device=resolved_user_agent,
            )

            await self.uow.commit()

        await self.session_service.activate_session_in_cache(
            session_dto,
            user_dto,
        )

        await self.notifier.enrich_session(
            session_id=session_dto.session_id,
            ip=ip,
            user_agent=resolved_user_agent,
        )

        return user_dto, session_dto, access_token, refresh_token

    async def logout(
        self,
        user_id: str,
        refresh_token: str,
    ) -> None:
        """Завершает текущую пользовательскую сессию."""
        fingerprint = crypto.hash_token(refresh_token)
        session_id: UUID | None = None

        async with self.uow:
            session = await self.uow.sessions.get_by_fingerprint(fingerprint)

            if session:
                session_id = session.session_id
                await self.uow.sessions.revoke_by_id(
                    UUID(user_id),
                    session.session_id,
                )

            await self.notifier.notify_logout(user_id)
            await self.uow.commit()

        if session_id:
            await self.session_service.clear_session_cache(session_id)

    async def _check_password_with_min_delay(
        self,
        password: str,
        password_hash: str,
    ) -> bool:
        """Проверяет пароль и выравнивает минимальное время проверки."""
        start = monotonic()

        password_valid = await crypto.check_password(password, password_hash)

        elapsed = monotonic() - start
        if elapsed < MIN_PASSWORD_CHECK_SECONDS:
            await asyncio.sleep(MIN_PASSWORD_CHECK_SECONDS - elapsed)

        return password_valid

    async def _register_failed_attempt(self, user_id: UUID) -> None:
        """Регистрирует неуспешную попытку входа и блокирует аккаунт при лимите."""
        attempts_key = _get_login_attempts_key(user_id)

        failed_attempts = await self.redis.incr(attempts_key)
        await self.redis.expire(attempts_key, FAILED_LOGIN_TTL_SECONDS)

        if failed_attempts < FAILED_LOGIN_LIMIT:
            return

        async with self.uow:
            user = await self.uow.users.get_by_id(user_id)
            if user:
                user.is_locked = True
                user.locked_until = time.utc_now() + timedelta(
                    minutes=ACCOUNT_LOCK_MINUTES,
                )

                user_dto = user_to_dto(user)
                await self.notifier.notify_suspicious_activity(
                    user=user_dto,
                    reason="too_many_failed_login_attempts",
                    device=None,
                )

            await self.uow.commit()

        logger.warning(
            "User locked due to failed login attempts",
            extra={"user_id": str(user_id)},
        )


def _is_user_temporarily_locked(user) -> bool:
    """Проверяет, заблокирован ли пользователь в текущий момент."""
    return bool(
        user
        and user.is_locked
        and user.locked_until
        and user.locked_until > time.utc_now()
    )


def _get_login_attempts_key(user_id: UUID) -> str:
    """Возвращает Redis-ключ счетчика неуспешных попыток входа."""
    return f"auth:login_attempts:{user_id}"
