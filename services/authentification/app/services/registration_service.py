import logging
from uuid import uuid4

from redis.asyncio import Redis
from sqlalchemy.exc import IntegrityError

from app.core import config, exceptions
from app.domain.mappers.session import session_to_dto
from app.domain.mappers.user import user_to_dto
from app.domain.schemas import api as api_schemas
from app.domain.schemas.dtos import SessionDTO, UserDTO
from app.infrastructure.db import models, uow
from app.services.notifier import AuthNotifier
from app.services.session_service import SessionService
from app.utils import crypto, redis_keys

logger = logging.getLogger(__name__)
settings = config.settings


class RegistrationService:
    """Сервис регистрации пользователей."""

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

    async def start_email_verification(self, email: str) -> str:
        """Проверяет email и отправляет письмо с токеном верификации."""
        normalized_email = email.lower().strip()

        async with self.uow:
            existing_user = await self.uow.users.get_by_email(normalized_email)
            if existing_user:
                return "sign_in"

        token = str(uuid4())
        hashed_token = crypto.hash_token(token)
        redis_key = redis_keys.get_verify_email_key(normalized_email)

        await self.redis.set(
            redis_key,
            hashed_token,
            ex=settings.JWT.EMAIL_TOKEN_EXPIRE_SECONDS,
        )

        async with self.uow:
            await self.notifier.send_verification_email(normalized_email, token)
            await self.uow.commit()

        return "sign_up"

    async def validate_email_verification_token(
        self,
        token: str,
        email: str,
    ) -> None:
        """Проверяет токен верификации email."""
        normalized_email = email.lower().strip()
        redis_key = redis_keys.get_verify_email_key(normalized_email)
        stored_hash = await self.redis.get(redis_key)

        if not stored_hash:
            raise exceptions.InvalidTokenError("Invalid or expired token")

        is_valid = crypto.secure_compare(
            stored_hash,
            crypto.hash_token(token),
        )
        if not is_valid:
            raise exceptions.InvalidTokenError("Invalid or expired token")

        async with self.uow:
            await self.notifier.notify_email_verified(normalized_email)
            await self.uow.commit()

    async def complete_registration(
        self,
        body: api_schemas.CompleteRegistrationRequest,
        ip: str,
        user_agent: str | None,
    ) -> tuple[UserDTO, SessionDTO, str, str]:
        """Создает пользователя, сессию и пару access/refresh токенов."""
        normalized_email = body.email.lower().strip()
        resolved_user_agent = user_agent or "Unknown"

        await self.validate_email_verification_token(
            body.token,
            normalized_email,
        )

        device_name = "Detecting..."
        location = "Unknown"
        password_hash = await crypto.hash_password(body.password)

        try:
            async with self.uow:
                user = models.User(
                    user_id=uuid4(),
                    email=normalized_email,
                    name=body.name,
                    language=body.language.value,
                    gender=body.gender.value if body.gender else None,
                    password_hash=password_hash,
                    is_active=True,
                    role=api_schemas.UserRole.USER.value,
                )

                self.uow.users.create(user)
                await self.uow.flush()

                (
                    access_token,
                    refresh_token,
                    session,
                ) = await self.session_service.create_session_and_tokens(
                    user=user,
                    user_agent=resolved_user_agent,
                    device_name=device_name,
                    ip=ip,
                    location=location,
                )

                user_dto = user_to_dto(user)
                session_dto = session_to_dto(session)
                session_dto.is_current = True

                await self.notifier.notify_registration(
                    user_dto,
                    ip,
                    location,
                )

                await self.uow.commit()

        except IntegrityError as exc:
            if _is_email_unique_violation(exc):
                raise exceptions.EmailAlreadyExistsError(
                    "Email already registered",
                ) from exc

            logger.error("Registration integrity error: %s", exc, exc_info=True)
            raise exceptions.DatabaseError("Registration failed") from exc

        await self.session_service.activate_session_in_cache(
            session_dto,
            user_dto,
        )

        await self.redis.delete(redis_keys.get_verify_email_key(normalized_email))

        await self.notifier.enrich_session(
            session_id=session_dto.session_id,
            ip=ip,
            user_agent=resolved_user_agent,
        )

        return user_dto, session_dto, access_token, refresh_token


def _is_email_unique_violation(exc: IntegrityError) -> bool:
    """Проверяет, связана ли IntegrityError с уникальностью email."""
    error_text = str(exc)
    return "uq_users_email" in error_text or "UniqueViolation" in error_text
