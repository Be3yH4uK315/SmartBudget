import asyncio
from uuid import uuid4, UUID

from redis.asyncio import Redis

from app.core import exceptions, config
from app.infrastructure.db import uow
from app.domain.schemas import api as api_schemas
from app.domain.schemas.dtos import UserDTO
from app.domain.mappers.user import user_to_dto
from app.services.session_service import SessionService
from app.services.notifier import AuthNotifier
from app.utils import redis_keys, crypto


settings = config.settings


class PasswordService:
    """Сервис управления паролями."""

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

    async def start_password_reset(self, email: str) -> None:
        """Старт сброса пароля."""
        async with self.uow:
            user = await self.uow.users.get_by_email(email)
            user_exists = user is not None

        if user_exists:
            token = str(uuid4())
            hashed_token = crypto.hash_token(token)

            await self.redis.set(
                redis_keys.get_reset_password_key(email),
                hashed_token,
                ex=settings.JWT.EMAIL_TOKEN_EXPIRE_SECONDS,
            )

            await self.notifier.send_password_reset_email(
                email,
                token,
            )
        else:
            await asyncio.sleep(0.05)

    async def validate_password_reset_token(
        self,
        token: str,
        email: str,
    ) -> None:
        redis_key = redis_keys.get_reset_password_key(email)
        stored_hash = await self.redis.get(redis_key)

        if (
            not stored_hash
            or not crypto.secure_compare(
                stored_hash,
                crypto.hash_token(token),
            )
        ):
            raise exceptions.InvalidTokenError(
                "Invalid or expired token"
            )

        async with self.uow:
            await self.notifier.notify_password_reset_validated(
                email
            )

    async def complete_password_reset(
        self,
        body: api_schemas.CompleteResetRequest,
    ) -> None:
        await self.validate_password_reset_token(
            body.token,
            body.email,
        )

        new_hash = await crypto.hash_password(
            body.new_password
        )

        user_id_to_revoke: UUID | None = None
        user_dto: UserDTO | None = None

        async with self.uow:
            user = await self.uow.users.get_by_email(
                body.email
            )
            if not user:
                raise exceptions.UserNotFoundError(
                    "User not found"
                )

            self.uow.users.update_password(
                user,
                new_hash,
            )

            user_id_to_revoke = user.user_id
            user_dto = user_to_dto(user)

            await self.notifier.notify_password_reset_completed(
                user_dto
            )

            await self.uow.commit()

        if user_id_to_revoke:
            await self.session_service.revoke_all_user_sessions(
                user_id_to_revoke
            )
            await self.session_service.invalidate_user_cache(
                user_id_to_revoke
            )

        await self.redis.delete(
            redis_keys.get_reset_password_key(body.email)
        )

    async def change_password(
        self,
        user_id: UUID,
        body: api_schemas.ChangePasswordRequest,
    ) -> None:
        async with self.uow:
            user = await self.uow.users.get_by_id(user_id)
            if not user:
                raise exceptions.InvalidCredentialsError(
                    "User not found"
                )

            is_valid = await crypto.check_password(
                body.password,
                user.password_hash,
            )
            if not is_valid:
                raise exceptions.InvalidCredentialsError(
                    "Invalid current password"
                )

            new_hash = await crypto.hash_password(
                body.new_password
            )

            self.uow.users.update_password(
                user,
                new_hash,
            )

            await self.notifier.notify_password_changed(
                str(user_id)
            )

            await self.uow.commit()
        
        await self.session_service.revoke_all_user_sessions(
            user_id
        )
        await self.session_service.invalidate_user_cache(
            user_id
        )