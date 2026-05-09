import logging
from uuid import UUID, uuid4

import orjson
from redis.asyncio import Redis
from sqlalchemy.exc import IntegrityError

from app.core import config, exceptions
from app.domain.mappers.user import user_to_dto
from app.domain.schemas import api as api_schemas
from app.domain.schemas.dtos import UserDTO
from app.infrastructure.db import uow
from app.services.notifier import AuthNotifier
from app.services.session_service import SessionService
from app.utils import crypto, redis_keys

logger = logging.getLogger(__name__)
settings = config.settings


class ProfileService:
    """Сервис управления профилем пользователя."""

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

    async def update_profile(
        self,
        user_id: UUID,
        body: api_schemas.UpdateProfileRequest,
    ) -> UserDTO:
        """Обновляет имя и пол пользователя."""
        new_gender = body.gender.value if body.gender else None

        async with self.uow:
            user = await self.uow.users.get_by_id(user_id)
            if not user:
                raise exceptions.UserNotFoundError("User not found")

            if user.name == body.name and user.gender == new_gender:
                return user_to_dto(user)

            await self.uow.users.update_profile_data(
                user_id=user_id,
                name=body.name,
                gender=new_gender,
            )
            await self.uow.refresh(user)

            user_dto = user_to_dto(user)

            await self.notifier.notify_profile_updated(
                str(user_id),
                email=user_dto.email,
                language=user_dto.language.value,
            )
            await self.uow.commit()

        await self.session_service.invalidate_user_cache(user_id)
        await self.session_service.cache_user_data(user_dto)

        return user_dto

    async def update_language(
        self,
        user_id: UUID,
        body: api_schemas.UpdateLanguageRequest,
    ) -> UserDTO:
        """Обновляет язык интерфейса пользователя."""
        async with self.uow:
            user = await self.uow.users.get_by_id(user_id)
            if not user:
                raise exceptions.UserNotFoundError("User not found")

            if user.language == body.language.value:
                return user_to_dto(user)

            await self.uow.users.update_language(user_id, body.language.value)
            await self.uow.refresh(user)

            user_dto = user_to_dto(user)

            await self.notifier.notify_profile_updated(
                str(user_id),
                email=user_dto.email,
                language=user_dto.language.value,
            )
            await self.uow.commit()

        await self.session_service.invalidate_user_cache(user_id)
        await self.session_service.cache_user_data(user_dto)

        return user_dto

    async def initiate_email_change(
        self,
        user_id: UUID,
        body: api_schemas.InitiateEmailChangeRequest,
    ) -> None:
        """Создает токен смены email и отправляет письмо подтверждения."""
        new_email = body.new_email.lower().strip()

        async with self.uow:
            user = await self.uow.users.get_by_id(user_id)
            if not user:
                raise exceptions.UserNotFoundError("User not found")

            if user.email == new_email:
                raise exceptions.InvalidCredentialsError(
                    "New email is same as current",
                )

            password_valid = await crypto.check_password(
                body.password,
                user.password_hash,
            )
            if not password_valid:
                raise exceptions.InvalidCredentialsError("Invalid password")

            existing_user = await self.uow.users.get_by_email(new_email)
            if existing_user:
                raise exceptions.EmailAlreadyExistsError("Email already in use")

        token = str(uuid4())
        hashed_token = crypto.hash_token(token)
        redis_key = redis_keys.get_change_email_key(hashed_token)

        change_data = {
            "user_id": str(user_id),
            "new_email": new_email,
        }

        await self.redis.set(
            redis_key,
            orjson.dumps(change_data),
            ex=settings.JWT.EMAIL_TOKEN_EXPIRE_SECONDS,
        )

        async with self.uow:
            await self.notifier.send_change_email_confirmation(
                new_email,
                token,
                str(user_id),
            )
            await self.uow.commit()

    async def confirm_email_change(
        self,
        body: api_schemas.ConfirmEmailChangeRequest,
    ) -> UserDTO:
        """Подтверждает смену email по токену."""
        hashed_token = crypto.hash_token(body.token)
        redis_key = redis_keys.get_change_email_key(hashed_token)

        data_raw = await self.redis.get(redis_key)
        if not data_raw:
            raise exceptions.InvalidTokenError("Invalid or expired token")

        user_id, new_email = _parse_email_change_token_data(data_raw)

        async with self.uow:
            user = await self.uow.users.get_by_id(user_id)
            if not user:
                raise exceptions.UserNotFoundError("User not found")

            old_email = user.email

            try:
                await self.uow.users.update_email(user_id, new_email)
                await self.uow.refresh(user)

                user_dto = user_to_dto(user)

                await self.notifier.notify_email_changed(
                    str(user_id),
                    old_email,
                    new_email,
                )
                await self.uow.commit()

            except IntegrityError as exc:
                raise exceptions.EmailAlreadyExistsError(
                    "Email already in use",
                ) from exc

        await self.redis.delete(redis_key)
        await self.session_service.invalidate_user_cache(user_id)
        await self.session_service.revoke_all_user_sessions(user_id)

        return user_dto


def _parse_email_change_token_data(data_raw: str | bytes) -> tuple[UUID, str]:
    """Извлекает user_id и new_email из данных токена смены email."""
    try:
        data = orjson.loads(data_raw)
        user_id = UUID(data["user_id"])
        new_email = str(data["new_email"]).lower().strip()
    except Exception as exc:
        raise exceptions.InvalidTokenError("Token data corrupted") from exc

    return user_id, new_email
