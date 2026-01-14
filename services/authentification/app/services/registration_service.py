import logging
from uuid import uuid4

from redis.asyncio import Redis
from sqlalchemy.exc import IntegrityError

from app.domain.mappers.session import session_to_dto
from app.domain.mappers.user import user_to_dto
from app.domain.schemas.dtos import SessionDTO, UserDTO
from app.infrastructure.db import models, uow
from app.core import exceptions, config
from app.domain.schemas import api as api_schemas
from app.utils import redis_keys, crypto
from app.services.session_service import SessionService
from app.services.notifier import AuthNotifier

logger = logging.getLogger(__name__)
settings = config.settings

class RegistrationService:
    """Сервис регистрации."""
    
    def __init__(
        self,
        uow: uow.UnitOfWork,
        redis: Redis,
        session_service: SessionService,
        notifier: AuthNotifier
    ):
        self.uow = uow
        self.redis = redis
        self.session_service = session_service
        self.notifier = notifier

    async def start_email_verification(self, email: str) -> str:
        """Проверяет email и отправляет письмо."""
        async with self.uow:
            existing_user = await self.uow.users.get_by_email(email)
            if existing_user:
                return "sign_in"

        token = str(uuid4())
        hashed_token = crypto.hash_token(token)
        redis_key = redis_keys.get_verify_email_key(email)
        
        await self.redis.set(redis_key, hashed_token, ex=settings.JWT.EMAIL_TOKEN_EXPIRE_SECONDS)
        await self.notifier.send_verification_email(email, token)

        return "sign_up"

    async def validate_email_verification_token(self, token: str, email: str) -> None:
        """Проверяет токен верификации."""
        redis_key = redis_keys.get_verify_email_key(email)
        stored_hash = await self.redis.get(redis_key)

        if not stored_hash or not crypto.secure_compare(stored_hash, crypto.hash_token(token)):
            raise exceptions.InvalidTokenError("Invalid or expired token")

        async with self.uow:
            await self.notifier.notify_email_verified(email)

    async def complete_registration(
        self, 
        body: api_schemas.CompleteRegistrationRequest,
        ip: str,
        user_agent: str | None
    ):
        """Завершает регистрацию: создает пользователя и сеанс."""
        await self.validate_email_verification_token(body.token, body.email)

        device_name = "Detecting..."
        location = "Unknown"
        password_hash = await crypto.hash_password(body.password)

        user_dto: UserDTO
        session_dto: SessionDTO
        access_token: str
        refresh_token: str
        
        try:
            async with self.uow:
                user = models.User(
                    user_id=uuid4(),
                    email=body.email,
                    name=body.name,
                    country=body.country,
                    password_hash=password_hash,
                    is_active=True,
                    role=api_schemas.UserRole.USER.value,
                )
                self.uow.users.create(user)
                await self.uow.flush()

                access_token, refresh_token, session_orm = await self.session_service.create_session_and_tokens(
                    user, user_agent or "Unknown", device_name, ip, location
                )

                user_dto = user_to_dto(user)
                session_dto = session_to_dto(session_orm)
                
                await self.notifier.notify_registration(user_dto, ip, location)

        except IntegrityError as e:
            if "uq_users_email" in str(e) or "UniqueViolation" in str(e):
                 raise exceptions.EmailAlreadyExistsError("Email already registered")
            logger.error(f"DB integrity error: {e}")
            raise exceptions.DatabaseError("Registration failed")
        
        await self.session_service.activate_session_in_cache(session_dto, user_dto)
        await self.redis.delete(redis_keys.get_verify_email_key(body.email))
        await self.notifier.enrich_session(
            session_id=session_dto.session_id, 
            ip=ip, 
            user_agent=user_agent or "Unknown"
        )

        return user_dto, session_dto, access_token, refresh_token