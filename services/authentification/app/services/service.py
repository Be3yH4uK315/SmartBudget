import logging
import asyncio
from uuid import UUID, uuid4
from datetime import datetime, timedelta, timezone

from redis.asyncio import Redis
from redis.exceptions import LockError
from jwt import encode, decode, PyJWTError
from dadata import Dadata
from arq.connections import ArqRedis
from sqlalchemy.exc import IntegrityError

from app.infrastructure.db import models, uow
from app.core import exceptions, config
from app.domain.schemas import api as api_schemas
from app.domain.schemas import kafka as k_schemas
from app.utils import email_templates, redis_keys, crypto, network, serialization

logger = logging.getLogger(__name__)
settings = config.settings

def _create_outbox_event(event_type: k_schemas.AuthEventTypes, **kwargs) -> dict:
    """Фабрика для создания событий Outbox."""
    return {"event_type": event_type.value, **kwargs}

class AuthService:
    """Сервис, инкапсулирующий бизнес-логику аутентификации."""
    
    def __init__(
        self,
        uow: uow.UnitOfWork,
        redis: Redis,
        arq_pool: ArqRedis,
        dadata_client: Dadata | None,
    ):
        self.uow = uow
        self.redis = redis
        self.arq_pool = arq_pool
        self.dadata_client = dadata_client

    async def _save_kafka_event(self, event_type: k_schemas.AuthEventTypes, **kwargs):
        """Хелпер для сохранения события в Outbox внутри текущей транзакции."""
        event_data = _create_outbox_event(event_type, **kwargs)
        await self.uow.users.add_outbox_event(
            topic=settings.KAFKA.KAFKA_AUTH_EVENTS_TOPIC,
            event_data=event_data
        )

    # --- PUBLIC METHODS ---

    async def start_email_verification(self, email: str) -> str:
        """Проверяет email и отправляет письмо."""
        async with self.uow:
            existing_user = await self.uow.users.get_by_email(email)
            if existing_user:
                return "sign_in"

        token = str(uuid4())
        hashed_token = crypto.hash_token(token)
        redis_key = redis_keys.get_verify_email_key(email)
        await self.redis.set(redis_key, hashed_token, ex=900)

        email_body = email_templates.get_verification_email_body(email, token)
        
        await self.arq_pool.enqueue_job(
            'send_email_task',
            to=email,
            subject="Verify your email for SmartBudget",
            body=email_body,
        )

        async with self.uow:
            await self._save_kafka_event(
                k_schemas.AuthEventTypes.VERIFICATION_STARTED, 
                email=email
            )
        
        return "sign_up"

    async def validate_email_verification_token(self, token: str, email: str) -> None:
        """Проверяет токен верификации."""
        redis_key = redis_keys.get_verify_email_key(email)
        stored_hash = await self.redis.get(redis_key)

        if not stored_hash or stored_hash != crypto.hash_token(token):
            raise exceptions.InvalidTokenError("Invalid or expired token")

        async with self.uow:
            await self._save_kafka_event(
                k_schemas.AuthEventTypes.VERIFICATION_VALIDATED, 
                email=email
            )

    async def complete_registration(
        self, 
        body: api_schemas.CompleteRegistrationRequest,
        ip: str,
        user_agent: str | None
    ):
        """Завершает регистрацию: создает пользователя и сеанс."""
        await self.validate_email_verification_token(body.token, body.email)

        device_name = network.parse_device(user_agent or "Unknown")
        location_data = await asyncio.to_thread(
            network.get_location, 
            ip, 
            self.dadata_client
        )
        location = location_data.get("full", "Unknown")
        password_hash = await crypto.hash_password(body.password)

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

                access_token, refresh_token, session = await self._create_session_and_tokens(
                    user, user_agent, device_name, ip, location
                )
                
                await self._save_kafka_event(
                    k_schemas.AuthEventTypes.USER_REGISTERED,
                    user_id=str(user.user_id),
                    email=user.email,
                    name=user.name,
                    ip=ip,
                    location=location
                )
        except IntegrityError as e:
            if "uq_users_email" in str(e) or "UniqueViolation" in str(e):
                 raise exceptions.EmailAlreadyExistsError("Email already registered")
            logger.error(f"Database integrity error during registration: {e}")
            raise exceptions.DatabaseError("Registration failed due to database error")

        await self.redis.delete(redis_keys.get_verify_email_key(body.email))
        return user, session, access_token, refresh_token

    async def authenticate_user(
        self, 
        body: api_schemas.LoginRequest, 
        ip: str,
        user_agent: str | None
    ):
        """Вход в систему."""
        location_data = await asyncio.to_thread(
            network.get_location, 
            ip, 
            self.dadata_client
        )
        location = location_data.get("full", "Unknown")

        user_id = None
        password_hash = None
        is_active = False
        
        async with self.uow:
            user = await self.uow.users.get_by_email(body.email)
            if user:
                user_id = user.user_id
                password_hash = user.password_hash
                is_active = user.is_active

        target_hash = password_hash if user_id else settings.APP.DUMMY_HASH
        password_valid = await crypto.check_password(body.password, target_hash)

        if not user_id:
            password_valid = False

        async with self.uow:
            user = None
            if user_id:
                user = await self.uow.users.get_by_id(user_id)

            if not user or not is_active or not password_valid:
                await self._save_kafka_event(
                    k_schemas.AuthEventTypes.USER_LOGIN_FAILED,
                    email=body.email,
                    ip=ip,
                    location=location
                )
                raise exceptions.InvalidCredentialsError("Invalid credentials")

            device_name = network.parse_device(user_agent or "Unknown")
            access_token, refresh_token, session = await self._create_session_and_tokens(
                user, user_agent, device_name, ip, location
            )
            
            await self.uow.users.update_last_login(user.user_id)

            await self._save_kafka_event(
                k_schemas.AuthEventTypes.USER_LOGIN,
                user_id=str(user.user_id),
                email=user.email,
                ip=ip,
                location=location
            )

        return user, session, access_token, refresh_token

    async def logout(self, user_id: str, refresh_token: str) -> None:
        """Выход из системы."""
        fingerprint = crypto.hash_token(refresh_token)
        async with self.uow:
            session = await self.uow.sessions.get_by_fingerprint(fingerprint)
            
            if session:
                await self.uow.sessions.revoke_by_fingerprint(UUID(user_id), fingerprint)
                await self.redis.delete(redis_keys.get_session_key(str(session.session_id)))
            
            await self._save_kafka_event(
                k_schemas.AuthEventTypes.USER_LOGOUT,
                user_id=user_id
            )

    async def start_password_reset(self, email: str) -> None:
        """Начало сброса пароля."""
        async with self.uow:
            user = await self.uow.users.get_by_email(email)

        token = str(uuid4())
        hashed_token = crypto.hash_token(token)
        if user:
            await self.redis.set(
                redis_keys.get_reset_password_key(email),
                hashed_token,
                ex=900,
            )
            await self.arq_pool.enqueue_job(
                "send_email_task",
                to=email,
                subject="Reset your password",
                body=email_templates.get_password_reset_body(email, token),
            )
            async with self.uow:
                await self._save_kafka_event(
                    k_schemas.AuthEventTypes.PASSWORD_RESET_STARTED,
                    email=email
                )
        else:
            await asyncio.sleep(0.05)


    async def validate_password_reset_token(self, token: str, email: str) -> None:
        """Валидация токена сброса."""
        redis_key = redis_keys.get_reset_password_key(email)
        stored_hash = await self.redis.get(redis_key)

        if not stored_hash or stored_hash != crypto.hash_token(token):
            raise exceptions.InvalidTokenError("Invalid or expired token")

        async with self.uow:
            await self._save_kafka_event(
                k_schemas.AuthEventTypes.PASSWORD_RESET_VALIDATED,
                email=email
            )

    async def complete_password_reset(self, body: api_schemas.CompleteResetRequest) -> None:
        """Завершение сброса пароля."""
        await self.validate_password_reset_token(body.token, body.email)

        new_hash = await crypto.hash_password(body.new_password)

        async with self.uow:
            user = await self.uow.users.get_by_email(body.email)
            if not user:
                raise exceptions.UserNotFoundError("User not found")

            self.uow.users.update_password(user, new_hash)
            await self.uow.sessions.revoke_all_for_user(user.user_id)

            await self._save_kafka_event(
                k_schemas.AuthEventTypes.PASSWORD_RESET_COMPLETED,
                user_id=str(user.user_id),
                email=user.email
            )

        await self.redis.delete(redis_keys.get_reset_password_key(body.email))

    async def change_password(self, user_id: UUID, body: api_schemas.ChangePasswordRequest) -> None:
        """Смена пароля."""
        async with self.uow:
            user = await self.uow.users.get_by_id(user_id)
            if not user:
                 raise exceptions.InvalidCredentialsError("User not found")
            
            is_valid = await crypto.check_password(body.password, user.password_hash)
            
            if not is_valid:
                raise exceptions.InvalidCredentialsError("Invalid current password")

            new_hash = await crypto.hash_password(body.new_password)
            
            self.uow.users.update_password(user, new_hash)
            await self.uow.sessions.revoke_all_for_user(user.user_id)

            await self._save_kafka_event(
                k_schemas.AuthEventTypes.PASSWORD_CHANGED,
                user_id=str(user_id)
            )

    async def update_session_activity(self, session_id: UUID):
        """Обновляет last_activity сессии."""
        throttle_key = f"session:throttle_activity:{session_id}"

        should_update_db = await self.redis.set(throttle_key, "1", ex=300, nx=True)

        if should_update_db:
            now = datetime.now(timezone.utc)
            async with self.uow:
                await self.uow.sessions.update_last_activity(session_id, now)

    async def get_all_sessions(
        self, user_id: UUID, current_refresh_token: str | None
    ) -> list[api_schemas.SessionInfo]:
        """Получение всех сессий пользователя."""
        current_fingerprint = crypto.hash_token(current_refresh_token) if current_refresh_token else None
        async with self.uow:
            sessions = await self.uow.sessions.get_all_active(user_id)

        return [
            api_schemas.SessionInfo(
                session_id=s.session_id,
                device_name=s.device_name,
                location=s.location,
                ip=s.ip,
                created_at=s.created_at,
                is_current_session=(s.refresh_fingerprint == current_fingerprint),
            )
            for s in sessions
        ]

    async def revoke_session_by_id(self, user_id: UUID, session_id: str) -> None:
        """Отзывает сессию по ее ID."""
        async with self.uow:
            await self.uow.sessions.revoke_by_id(user_id, UUID(session_id))
            await self._save_kafka_event(
                k_schemas.AuthEventTypes.SESSION_REVOKED,
                user_id=str(user_id),
                session_id=session_id
            )

    async def revoke_other_sessions(self, user_id: UUID, current_refresh_token: str) -> None:
        """Отзывает все сессии, кроме текущей."""
        async with self.uow:
            await self.uow.sessions.revoke_all_except(
                user_id, crypto.hash_token(current_refresh_token)
            )

    async def validate_access_token(self, token: str) -> None:
        """Валидирует access token и проверяет активность сессии."""
        try:
            payload = decode(
                token,
                settings.JWT.JWT_PUBLIC_KEY,
                algorithms=[settings.JWT.JWT_ALGORITHM],
                issuer="auth-service",
                audience="smart-budget",
            )
            
            session_id = payload.get("sid")
            if not session_id:
                raise exceptions.InvalidTokenError("Token missing session ID")
            
            is_active = await self.redis.exists(redis_keys.get_session_key(session_id))
            if not is_active:
                raise exceptions.InvalidTokenError("Session revoked or expired")
                
        except PyJWTError as e:
            raise exceptions.InvalidTokenError(str(e))

    async def refresh_session(self, refresh_token: str):
        """Обновляет сессию и выдает новые токены."""
        fingerprint = crypto.hash_token(refresh_token)
        lock_key = f"lock:refresh:{fingerprint}"
        try:
            async with self.redis.lock(lock_key, timeout=5, blocking_timeout=2):
                async with self.uow:
                    session = await self.uow.sessions.get_by_fingerprint(fingerprint)
                    if not session:
                        raise exceptions.InvalidTokenError("Invalid refresh token (or already used)")

                    if session.expires_at < datetime.now(timezone.utc):
                        raise exceptions.InvalidTokenError("Refresh token expired")

                role = await self.uow.users.get_role_by_id(session.user_id)
                user = await self.uow.users.get_by_id(session.user_id)
                new_refresh_token = str(uuid4())
                new_fingerprint = crypto.hash_token(new_refresh_token)

                await self.uow.sessions.update_fingerprint(
                    session, new_fingerprint, datetime.now(timezone.utc) + timedelta(days=30)
                )

                await self._cache_session(session, user)

                new_access_token = self._create_access_token(
                    str(session.user_id), role, str(session.session_id)
                )

                await self._save_kafka_event(
                    k_schemas.AuthEventTypes.TOKEN_REFRESHED,
                    user_id=str(session.user_id)
                )
            return new_access_token, new_refresh_token
            
        except LockError:
            raise exceptions.TooManyAttemptsError("Refresh already in progress")

    def _create_access_token(self, user_id: str, role: int, session_id: str) -> str:
        payload = {
            "sub": user_id,
            "sid": session_id,
            "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
            "role": api_schemas.UserRole(role).value,
            "iss": "auth-service",
            "aud": "smart-budget",
        }
        return encode(
            payload,
            settings.JWT.JWT_PRIVATE_KEY,
            algorithm=settings.JWT.JWT_ALGORITHM,
        )
    
    async def _cache_session(self, session: models.Session, user: models.User):
        """Кэширует сессию в Redis для быстрой валидации."""
        session_data = {
            "user_id": str(user.user_id),
            "role": user.role,
            "is_active": user.is_active,
            "session_id": str(session.session_id)
        }
        key = redis_keys.get_session_key(str(session.session_id))
        await self.redis.set(key, serialization.to_json_str(session_data), ex=timedelta(days=30))

    async def _create_session_and_tokens(
        self,
        user: models.User,
        user_agent: str | None,
        device_name: str,
        ip: str,
        location: str,
    ):
        refresh_token = str(uuid4())
        fingerprint = crypto.hash_token(refresh_token)
        now = datetime.now(timezone.utc)
        session = models.Session(
            session_id=uuid4(),
            user=user,
            user_agent=user_agent or "Unknown",
            device_name=device_name,
            ip=ip,
            location=location,
            revoked=False,
            refresh_fingerprint=fingerprint,
            last_activity=now,
            expires_at=now + timedelta(days=30),
            created_at=now,
        )
        self.uow.sessions.create(session)
        
        await self._cache_session(session, user)
        
        access_token = self._create_access_token(str(user.user_id), user.role, str(session.session_id))
        
        return access_token, refresh_token, session