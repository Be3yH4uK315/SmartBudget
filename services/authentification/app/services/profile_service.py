import logging
import orjson
from uuid import uuid4, UUID
from sqlalchemy.exc import IntegrityError
from redis.asyncio import Redis

from app.core import exceptions, config
from app.infrastructure.db import uow
from app.domain.schemas import api as api_schemas
from app.domain.schemas.dtos import UserDTO
from app.domain.mappers.user import user_to_dto
from app.services.session_service import SessionService
from app.services.notifier import AuthNotifier
from app.utils import redis_keys, crypto

logger = logging.getLogger(__name__)
settings = config.settings

class ProfileService:
    """Сервис управления профилем пользователя (Имя, Email)."""

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

    async def update_profile(
        self,
        user_id: UUID,
        body: api_schemas.UpdateProfileRequest
    ) -> UserDTO:
        """Обновление профиля."""
        async with self.uow:
            user = await self.uow.users.get_by_id(user_id)
            if not user:
                raise exceptions.UserNotFoundError("User not found")
            
            new_gender = body.gender.value if body.gender else None
            current_gender = user.gender
            
            if user.name == body.name and current_gender == new_gender:
                return user_to_dto(user)

            await self.uow.users.update_profile_data(
                user_id, 
                name=body.name if body.name else None,
                gender=new_gender
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
        body: api_schemas.UpdateLanguageRequest
    ) -> UserDTO:
        """Обновление языка интерфейса."""
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

    async def update_language(
        self,
        user_id: UUID,
        body: api_schemas.UpdateLanguageRequest
    ) -> UserDTO:
        """Обновление языка интерфейса."""
        async with self.uow:
            user = await self.uow.users.get_by_id(user_id)
            if not user:
                raise exceptions.UserNotFoundError("User not found")

            if user.language == body.language.value:
                return user_to_dto(user)

            await self.uow.users.update_language(user_id, body.language.value)
            await self.uow.refresh(user)
            user_dto = user_to_dto(user)
            await self.notifier.notify_profile_updated(str(user_id))
            await self.uow.commit()

        await self.session_service.invalidate_user_cache(user_id)
        await self.session_service.cache_user_data(user_dto)

        return user_dto

    async def initiate_email_change(
        self,
        user_id: UUID,
        body: api_schemas.InitiateEmailChangeRequest
    ) -> None:
        """Инициация смены email."""
        new_email = body.new_email.lower().strip()

        async with self.uow:
            user = await self.uow.users.get_by_id(user_id)
            if not user:
                raise exceptions.UserNotFoundError("User not found")

            if user.email == new_email:
                raise exceptions.InvalidCredentialsError("New email is same as current")

            is_valid = await crypto.check_password(body.password, user.password_hash)
            if not is_valid:
                raise exceptions.InvalidCredentialsError("Invalid password")

            existing_user = await self.uow.users.get_by_email(new_email)
            if existing_user:
                raise exceptions.EmailAlreadyExistsError("Email already in use")

        token = str(uuid4())
        hashed_token = crypto.hash_token(token)
        
        change_data = {
            "user_id": str(user_id),
            "new_email": new_email
        }
        
        redis_key = redis_keys.get_change_email_key(hashed_token)

        await self.redis.set(
            redis_key, 
            orjson.dumps(change_data), 
            ex=settings.JWT.EMAIL_TOKEN_EXPIRE_SECONDS
        )

        await self.notifier.send_change_email_confirmation(new_email, token, str(user_id))

    async def confirm_email_change(
        self,
        body: api_schemas.ConfirmEmailChangeRequest
    ) -> UserDTO:
        """Подтверждение смены email по токену."""
        token = body.token
        hashed_token = crypto.hash_token(token)
        redis_key = redis_keys.get_change_email_key(hashed_token)

        data_raw = await self.redis.get(redis_key)
        if not data_raw:
            raise exceptions.InvalidTokenError("Invalid or expired token")

        try:
            data = orjson.loads(data_raw)
            user_id = UUID(data["user_id"])
            new_email = data["new_email"]
        except Exception:
            raise exceptions.InvalidTokenError("Token data corrupted")

        async with self.uow:
            user = await self.uow.users.get_by_id(user_id)
            if not user:
                raise exceptions.UserNotFoundError("User not found")
            
            old_email = user.email

            try:
                await self.uow.users.update_email(user_id, new_email)
                await self.uow.refresh(user)
                user_dto = user_to_dto(user)
                await self.notifier.notify_email_changed(str(user_id), old_email, new_email)
                await self.uow.commit()

            except IntegrityError:
                raise exceptions.EmailAlreadyExistsError("Email already in use")
        
        await self.redis.delete(redis_key)
        await self.session_service.invalidate_user_cache(user_id)
        await self.session_service.revoke_all_user_sessions(user_id)
        
        return user_dto
