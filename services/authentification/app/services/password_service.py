import asyncio
from uuid import UUID, uuid4

from redis.asyncio import Redis

from app.core import config, exceptions
from app.domain.mappers.user import user_to_dto
from app.domain.schemas import api as api_schemas
from app.infrastructure.db import uow
from app.services.notifier import AuthNotifier
from app.services.session_service import SessionService
from app.utils import crypto, redis_keys

settings = config.settings

PASSWORD_RESET_FAKE_DELAY_SECONDS = 0.05


class PasswordService:
    """Сервис управления паролями."""

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

    async def start_password_reset(self, email: str) -> None:
        """Запускает сценарий сброса пароля."""
        normalized_email = email.lower().strip()

        async with self.uow:
            user = await self.uow.users.get_by_email(normalized_email)

        if not user:
            await asyncio.sleep(PASSWORD_RESET_FAKE_DELAY_SECONDS)
            return

        token = str(uuid4())
        hashed_token = crypto.hash_token(token)

        await self.redis.set(
            redis_keys.get_reset_password_key(normalized_email),
            hashed_token,
            ex=settings.JWT.EMAIL_TOKEN_EXPIRE_SECONDS,
        )

        async with self.uow:
            await self.notifier.send_password_reset_email(
                normalized_email,
                token,
            )
            await self.uow.commit()

    async def validate_password_reset_token(
        self,
        token: str,
        email: str,
    ) -> None:
        """Проверяет токен сброса пароля."""
        normalized_email = email.lower().strip()
        redis_key = redis_keys.get_reset_password_key(normalized_email)
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
            await self.notifier.notify_password_reset_validated(normalized_email)
            await self.uow.commit()

    async def complete_password_reset(
        self,
        body: api_schemas.CompleteResetRequest,
    ) -> None:
        """Завершает сброс пароля и отзывает все сессии пользователя."""
        normalized_email = body.email.lower().strip()

        await self.validate_password_reset_token(
            body.token,
            normalized_email,
        )

        new_hash = await crypto.hash_password(body.new_password)

        async with self.uow:
            user = await self.uow.users.get_by_email(normalized_email)
            if not user:
                raise exceptions.UserNotFoundError("User not found")

            self.uow.users.update_password(user, new_hash)

            user_id = user.user_id
            user_dto = user_to_dto(user)

            await self.notifier.notify_password_reset_completed(user_dto)
            await self.uow.commit()

        await self.session_service.revoke_all_user_sessions(user_id)
        await self.session_service.invalidate_user_cache(user_id)

        await self.redis.delete(redis_keys.get_reset_password_key(normalized_email))

    async def change_password(
        self,
        user_id: UUID,
        body: api_schemas.ChangePasswordRequest,
    ) -> None:
        """Меняет пароль текущего пользователя и отзывает все его сессии."""
        async with self.uow:
            user = await self.uow.users.get_by_id(user_id)
            if not user:
                raise exceptions.InvalidCredentialsError("User not found")

            password_valid = await crypto.check_password(
                body.password,
                user.password_hash,
            )
            if not password_valid:
                raise exceptions.InvalidCredentialsError("Invalid current password")

            new_hash = await crypto.hash_password(body.new_password)
            self.uow.users.update_password(user, new_hash)

            await self.notifier.notify_password_changed(
                user_id=str(user_id),
                email=user.email,
                language=user.language,
                name=user.name,
            )
            await self.uow.commit()

        await self.session_service.revoke_all_user_sessions(user_id)
        await self.session_service.invalidate_user_cache(user_id)
