import asyncio
from uuid import UUID, uuid4
from datetime import datetime, timedelta, timezone

from redis.asyncio import Redis
from jwt import encode, decode, PyJWTError
import geoip2.database
from arq.connections import ArqRedis

from app import (
    email_templates,
    redis_keys,
    schemas,
    models,
    utils,
    settings,
    exceptions,
    unit_of_work
)

class AuthService:
    """Сервис, инкапсулирующий всю бизнес-логику аутентификации."""
    def __init__(
        self,
        uow: unit_of_work.UnitOfWork,
        redis: Redis,
        arq_pool: ArqRedis,
        geoip_reader: geoip2.database.Reader,
    ):
        self.uow = uow
        self.redis = redis
        self.arq_pool = arq_pool
        self.geoip_reader = geoip_reader

    async def _enqueue_kafka_event(self, event: schemas.BaseAuthEvent):
        """Хелпер для отправки события в очередь Arq."""
        await self.arq_pool.enqueue_job(
            'send_kafka_event',
            topic=schemas.KafkaTopics.AUTH_EVENTS.value,
            event_data=event.model_dump(mode='json')
        )

    async def start_email_verification(self, email: str) -> str:
        """Проверяет, свободен ли email, и инициирует отправку письма с токеном верификации."""
        async with self.uow:
            existing_user = await self.uow.users.get_by_email(email)
            if existing_user:
                return "sign_in"

        token = str(uuid4())
        hashed_token = utils.hash_token(token)
        redis_key = redis_keys.get_verify_email_key(email)
        await self.redis.set(redis_key, hashed_token, ex=900)

        email_body = email_templates.get_verification_email_body(email, token)
        await self.arq_pool.enqueue_job(
            'send_email',
            to=email,
            subject="Verify your email for SmartBudget",
            body=email_body,
        )

        event = schemas.UserEvent(
            event=schemas.AuthEventTypes.VERIFICATION_STARTED,
            email=email
        )
        await self._enqueue_kafka_event(event)
        
        return "sign_up"

    async def validate_email_verification_token(self, token: str, email: str) -> None:
        """Проверяет валидность токена верификации из email."""
        redis_key = redis_keys.get_verify_email_key(email)
        stored_hash = await self.redis.get(redis_key)

        if not stored_hash or stored_hash != utils.hash_token(token):
            raise exceptions.InvalidTokenError("Invalid or expired token")

        event = schemas.UserEvent(
            event=schemas.AuthEventTypes.VERIFICATION_VALIDATED,
            email=email
        )
        await self._enqueue_kafka_event(event)

    async def validate_password_reset_token(self, token: str, email: str) -> None:
        """Проверяет валидность токена сброса пароля из email."""
        redis_key = redis_keys.get_reset_password_key(email)
        stored_hash = await self.redis.get(redis_key)

        if not stored_hash or stored_hash != utils.hash_token(token):
            raise exceptions.InvalidTokenError("Invalid or expired token")

        event = schemas.UserEvent(
            event=schemas.AuthEventTypes.PASSWORD_RESET_VALIDATED,
            email=email
        )
        await self._enqueue_kafka_event(event)

    async def complete_registration(
        self, 
        body: schemas.CompleteRegistrationRequest,
        ip: str,
        user_agent: str | None
    ):
        """Завершает регистрацию: создает пользователя и сеанс."""
        await self.validate_email_verification_token(body.token, body.email)

        device_name = utils.parse_device(user_agent or "Unknown")
        location_data = await asyncio.to_thread(utils.get_location, ip, self.geoip_reader)
        location = location_data.get("full", "Unknown")

        async with self.uow:
            user = models.User(
                user_id=uuid4(),
                email=body.email,
                name=body.name,
                country=body.country,
                password_hash=utils.hash_password(body.password),
                is_active=True,
                role=schemas.UserRole.USER.value,
            )
            self.uow.users.create(user)

            access_token, refresh_token, session = self._create_session_and_tokens(
                self.uow, user, user_agent, device_name, ip, location
            )

        await self.redis.delete(redis_keys.get_verify_email_key(body.email))

        event = schemas.UserRegisteredEvent(
            event=schemas.AuthEventTypes.USER_REGISTERED,
            user_id=user.user_id,
            email=user.email,
            name=user.name,
            ip=ip,
            location=location
        )
        await self._enqueue_kafka_event(event)

        return user, session, access_token, refresh_token

    async def authenticate_user(
        self, 
        body: schemas.LoginRequest, 
        ip: str,
        user_agent: str | None
    ):
        """Выполняет вход в систему: проверяет учетные данные и создает сеанс."""
        location_data = await asyncio.to_thread(utils.get_location, ip, self.geoip_reader)
        location = location_data.get("full", "Unknown")

        async with self.uow:
            user = await self.uow.users.get_by_email(body.email)

            if not user or not user.is_active or not utils.check_password(body.password, user.password_hash):
                event = schemas.UserEvent(
                    event=schemas.AuthEventTypes.USER_LOGIN_FAILED,
                    email=body.email,
                    ip=ip,
                    location=location
                )
                await self._enqueue_kafka_event(event)
                raise exceptions.InvalidCredentialsError("Invalid credentials")

            device_name = utils.parse_device(user_agent or "Unknown")
            access_token, refresh_token, session = self._create_session_and_tokens(
                self.uow, user, user_agent, device_name, ip, location
            )
            await self.uow.users.update_last_login(user.user_id)

        event = schemas.UserEvent(
            event=schemas.AuthEventTypes.USER_LOGIN,
            user_id=user.user_id,
            email=user.email,
            ip=ip,
            location=location
        )
        await self._enqueue_kafka_event(event)

        return user, session, access_token, refresh_token

    async def logout(self, user_id: str, refresh_token: str) -> None:
        """Производит выход из системы, отзывая сессию по refresh_token."""
        fingerprint = utils.hash_token(refresh_token)
        async with self.uow:
            await self.uow.sessions.revoke_by_fingerprint(UUID(user_id), fingerprint)

        event = schemas.UserEvent(
            event=schemas.AuthEventTypes.USER_LOGOUT,
            user_id=UUID(user_id)
        )
        await self._enqueue_kafka_event(event)

    async def start_password_reset(self, email: str) -> None:
        """Инициирует сброс пароля, если пользователь существует."""
        async with self.uow:
            user = await self.uow.users.get_by_email(email)
            if not user:
                return

        token = str(uuid4())
        await self.redis.set(
            redis_keys.get_reset_password_key(email),
            utils.hash_token(token),
            ex=900,
        )

        await self.arq_pool.enqueue_job(
            "send_email",
            to=email,
            subject="Reset your password",
            body=email_templates.get_password_reset_body(email, token),
        )

        event = schemas.UserEvent(
            event=schemas.AuthEventTypes.PASSWORD_RESET_STARTED,
            email=email
        )
        await self._enqueue_kafka_event(event)

    async def complete_password_reset(self, body: schemas.CompleteResetRequest) -> None:
        """Завершает сброс пароля: проверяет токен и обновляет хэш пароля."""
        await self.validate_password_reset_token(body.token, body.email)

        async with self.uow:
            user = await self.uow.users.get_by_email(body.email)
            if not user:
                raise exceptions.UserNotFoundError("User not found")

            self.uow.users.update_password(user, utils.hash_password(body.new_password))
            await self.uow.sessions.revoke_all_for_user(user.user_id)

        await self.redis.delete(redis_keys.get_reset_password_key(body.email))

        event = schemas.UserEvent(
            event=schemas.AuthEventTypes.PASSWORD_RESET_COMPLETED,
            user_id=user.user_id,
            email=user.email
        )
        await self._enqueue_kafka_event(event)

    async def change_password(self, user_id: UUID, body: schemas.ChangePasswordRequest) -> None:
        """Изменяет пароль пользователя, используя userId из токена."""
        async with self.uow:
            user = await self.uow.users.get_by_id(user_id)
            if not user or not utils.check_password(body.password, user.password_hash):
                raise exceptions.InvalidCredentialsError("Invalid current password")

            self.uow.users.update_password(user, utils.hash_password(body.new_password))
            await self.uow.sessions.revoke_all_for_user(user.user_id)

        event = schemas.UserEvent(
            event=schemas.AuthEventTypes.PASSWORD_CHANGED,
            user_id=user_id
        )
        await self._enqueue_kafka_event(event)

    async def get_all_sessions(
        self, user_id: UUID, current_refresh_token: str | None
    ) -> list[schemas.SessionInfo]:
        """Получает все активные сессии для пользователя и помечает, какая является текущей."""
        current_fingerprint = utils.hash_token(current_refresh_token) if current_refresh_token else None
        async with self.uow:
            sessions = await self.uow.sessions.get_all_active(user_id)

        return [
            schemas.SessionInfo(
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
        """Отзывает одну конкретную сессию по ID. Проверка userId для безопасности."""
        async with self.uow:
            await self.uow.sessions.revoke_by_id(user_id, UUID(session_id))

    async def revoke_other_sessions(self, user_id: UUID, current_refresh_token: str) -> None:
        """Отзывает все сессии пользователя, кроме текущей."""
        async with self.uow:
            await self.uow.sessions.revoke_all_except(
                user_id, utils.hash_token(current_refresh_token)
            )

    async def validate_access_token(self, token: str) -> None:
        """Валидирует access_token."""
        try:
            payload = decode(
                token,
                settings.settings.JWT.JWT_PUBLIC_KEY,
                algorithms=[settings.settings.JWT.JWT_ALGORITHM],
                issuer="auth-service",
                audience="smart-budget",
            )
            user_id = payload.get("sub")
            if not user_id:
                raise exceptions.InvalidTokenError("Invalid token")
            
            async with self.uow:
                user = await self.uow.users.get_by_id(UUID(user_id))
                if not user or not user.is_active:
                    raise exceptions.UserInactiveError()
        except PyJWTError as e:
            raise exceptions.InvalidTokenError(str(e))


    async def refresh_session(self, refresh_token: str):
        """Обновляет сеанс с помощью проверки."""
        fingerprint = utils.hash_token(refresh_token)
        async with self.uow:
            session = await self.uow.sessions.get_by_fingerprint(fingerprint)
            if not session:
                raise exceptions.InvalidTokenError("Invalid refresh token")
            if session.expires_at < datetime.now(timezone.utc):
                raise exceptions.InvalidTokenError("Refresh token expired")

            role = await self.uow.users.get_role_by_id(session.user_id)
            new_access_token = self._create_access_token(str(session.user_id), role)
            new_refresh_token = str(uuid4())
            new_fingerprint = utils.hash_token(new_refresh_token)

            await self.uow.sessions.update_fingerprint(
                session, new_fingerprint, datetime.now(timezone.utc) + timedelta(days=30)
            )

        event = schemas.UserEvent(
            event=schemas.AuthEventTypes.TOKEN_REFRESHED,
            user_id=session.user_id
        )
        await self._enqueue_kafka_event(event)

        return new_access_token, new_refresh_token

    def _create_access_token(self, user_id: str, role: int) -> str:
        payload = {
            "sub": user_id,
            "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
            "role": schemas.UserRole(role).name,
            "iss": "auth-service",
            "aud": "smart-budget",
        }
        return encode(
            payload,
            settings.settings.JWT.JWT_PRIVATE_KEY,
            algorithm=settings.settings.JWT.JWT_ALGORITHM,
        )
    
    def _create_session_and_tokens(
        self,
        uow: unit_of_work.UnitOfWork,
        user: models.User,
        user_agent: str | None,
        device_name: str,
        ip: str,
        location: str,
    ):
        """Создает новый сеанс и генерирует токены."""
        refresh_token = str(uuid4())
        fingerprint = utils.hash_token(refresh_token)
        session = models.Session(
            session_id=uuid4(),
            user_id=user.user_id,
            user_agent=user_agent or "Unknown",
            device_name=device_name,
            ip=ip,
            location=location,
            revoked=False,
            refresh_fingerprint=fingerprint,
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            created_at=datetime.now(timezone.utc),
        )
        uow.sessions.create(session)
        access_token = self._create_access_token(str(user.user_id), user.role)
        return access_token, refresh_token, session