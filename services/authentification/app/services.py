import asyncio
from fastapi import Depends
from redis.asyncio import Redis
from uuid import uuid4, UUID
from datetime import datetime, timedelta, timezone
from jwt import encode, decode, PyJWTError
import geoip2.database
from arq.connections import ArqRedis

from app import (
    email_templates, 
    middleware, 
    dependencies,
    redis_keys, 
    schemas, 
    models, 
    utils, 
    settings,
    exceptions,
    repositories
)

class AuthService:
    """Сервис, инкапсулирующий всю бизнес-логику аутентификации."""
    def __init__(
        self,
        user_repo: repositories.UserRepository = Depends(repositories.UserRepository),
        session_repo: repositories.SessionRepository = Depends(repositories.SessionRepository),
        redis: Redis = Depends(dependencies.get_redis),
        arq_pool: ArqRedis = Depends(dependencies.get_arq_pool),
        geoip_reader: geoip2.database.Reader = Depends(dependencies.get_geoip_reader)
    ):
        self.user_repo = user_repo
        self.session_repo = session_repo
        self.redis = redis
        self.arq_pool = arq_pool
        self.geoip_reader = geoip_reader

    async def start_email_verification(self, email: str):
        """Проверяет, свободен ли email, и инициирует отправку письма с токеном верификации."""
        existing_user = await self.user_repo.get_by_email(email)
        if existing_user:
            middleware.logger.warning(f"Verification attempt for existing email: {email}")
            return "sign_in"

        token = str(uuid4())
        hashed_token = utils.hash_token(token)
        redis_key = redis_keys.get_verify_email_key(email)
        await self.redis.set(redis_key, hashed_token, ex=900)  # 15 мин TTL

        email_body = email_templates.get_verification_email_body(email, token)
        
        middleware.logger.info(f"Arq pool in AuthService: {self.arq_pool}")
        middleware.logger.info(f"Enqueueing send_email_async to {email} in queue {settings.settings.app.arq_queue_name}")
        job = await self.arq_pool.enqueue_job(
            'send_email_async',
            to=email,
            subject="Verify your email for SmartBudget",
            body=email_body,
        )
        middleware.logger.info(f"Job enqueued: {job.job_id}")

        await self.arq_pool.enqueue_job(
            'send_kafka_event_async',
            topic="auth_events",
            event_data={"event": "user.verification_started", "email": email},
            schema_name="AUTH_EVENTS_SCHEMA"
        )
        return "sign_up"

    async def validate_email_verification_token(self, token: str, email: str):
        """Проверяет валидность токена верификации из email."""
        redis_key = redis_keys.get_verify_email_key(email)
        event_name = "user.verification_validated"

        stored_hash = await self.redis.get(redis_key)
        if not stored_hash or stored_hash != utils.hash_token(token):
            middleware.logger.warning(f"Invalid or expired token for verification on email: {email}")
            raise exceptions.InvalidTokenError("Invalid or expired token")

        await self.arq_pool.enqueue_job(
            'send_kafka_event_async',
            topic="auth_events",
            event_data={"event": event_name, "email": email},
            schema_name="AUTH_EVENTS_SCHEMA"
        )
        middleware.logger.info(f"Token validated for verification on email: {email}, event sent")

    async def validate_password_reset_token(self, token: str, email: str):
        """Проверяет валидность токена сброса пароля из email."""
        redis_key = redis_keys.get_reset_password_key(email)
        event_name = "user.password_reset_validated"

        stored_hash = await self.redis.get(redis_key)
        if not stored_hash or stored_hash != utils.hash_token(token):
            middleware.logger.warning(f"Invalid or expired token for reset on email: {email}")
            raise exceptions.InvalidTokenError("Invalid or expired token")

        await self.arq_pool.enqueue_job(
            'send_kafka_event_async',
            topic="auth_events",
            event_data={"event": event_name, "email": email},
            schema_name="AUTH_EVENTS_SCHEMA"
        )
        middleware.logger.info(f"Token validated for reset on email: {email}, event sent")

    async def complete_registration(
        self, 
        body: schemas.CompleteRegistrationRequest,
        ip: str,
        user_agent: str | None
    ):
        """Завершает регистрацию: создает пользователя и сеанс."""
        await self.validate_email_verification_token(body.token, body.email)
        redis_key = redis_keys.get_verify_email_key(body.email)
        user_model = models.User(
            id=uuid4(),
            email=body.email,
            name=body.name,
            country=body.country,
            password_hash=utils.hash_password(body.password),
            is_active=True,
            role=models.UserRole.USER.value
        )
        user = await self.user_repo.create(user_model)

        device_name = utils.parse_device(user_agent or "Unknown")
        location_data = await asyncio.to_thread(utils.get_location, ip, self.geoip_reader)
        location = location_data.get("full", "Unknown")

        access_token, refresh_token, session = await self._create_session_and_tokens(
            user, 
            user_agent or "Unknown",
            device_name, 
            ip, 
            location
        )

        await self.arq_pool.enqueue_job(
            'send_kafka_event_async',
            topic="auth_events",
            event_data={
                "event": "user.registered",
                "user_id": str(user.id),
                "email": user.email,
                "ip": ip,
                "location": location
            },
            schema_name="AUTH_EVENTS_SCHEMA"
        )
        await self.redis.delete(redis_key)
        return user, session, access_token, refresh_token

    async def authenticate_user(
        self, 
        body: schemas.LoginRequest, 
        ip: str,
        user_agent: str | None
    ):
        """Выполняет вход в систему: проверяет учетные данные и создает сеанс."""
        fail_key = redis_keys.get_login_fail_key(ip)
        fails = int(await self.redis.get(fail_key) or 0)
        if fails >= 5:
            raise exceptions.TooManyAttemptsError("Too many attempts, try later")

        location_data = await asyncio.to_thread(utils.get_location, ip, self.geoip_reader)
        location = location_data.get("full", "Unknown")

        user = await self.user_repo.get_by_email(body.email)

        if not user or not user.is_active or not utils.check_password(body.password, user.password_hash):
            await self.redis.incr(fail_key)
            await self.redis.expire(fail_key, 60)
            await self.arq_pool.enqueue_job(
                'send_kafka_event_async',
                topic="auth_events",
                event_data = {
                    "event": "user.login_failed",
                    "email": body.email,
                    "ip": ip,
                    "location": location,
                },
                schema_name="AUTH_EVENTS_SCHEMA"
            )
            raise exceptions.InvalidCredentialsError("Invalid credentials")

        await self.redis.delete(fail_key)
        device_name = utils.parse_device(user_agent or "Unknown")

        access_token, refresh_token, session = await self._create_session_and_tokens(
            user, 
            user_agent or "Unknown",
            device_name, 
            ip, 
            location
        )

        await self.user_repo.update_last_login(user.id)

        await self.arq_pool.enqueue_job(
            'send_kafka_event_async',
            topic="auth_events",
            event_data = {
                "event": "user.login",
                "user_id": str(user.id),
                "email": user.email,
                "ip": ip,
                "location": location,
            },
            schema_name="AUTH_EVENTS_SCHEMA"
        )
        return user, session, access_token, refresh_token

    async def logout(self, user_id: str, refresh_token: str):
        """Производит выход из системы, отзывая сессию по refresh_token."""
        if not refresh_token:
            raise exceptions.InvalidTokenError("Not authenticated (missing refresh token)")

        fingerprint = utils.hash_token(refresh_token)
        await self.session_repo.revoke_by_fingerprint(UUID(user_id), fingerprint)

        await self.arq_pool.enqueue_job(
            'send_kafka_event_async',
            topic="auth_events",
            event_data={"event": "user.logout", "user_id": user_id},
            schema_name="AUTH_EVENTS_SCHEMA"
        )

    async def start_password_reset(self, email: str):
        """Инициирует сброс пароля, если пользователь существует."""
        user = await self.user_repo.get_by_email(email)
        if not user:
            middleware.logger.warning(f"Password reset attempt for non-existing email: {email}")
            return

        token = str(uuid4())
        hashed_token = utils.hash_token(token)
        redis_key = redis_keys.get_reset_password_key(email)
        await self.redis.set(redis_key, hashed_token, ex=900)
        
        email_body = email_templates.get_password_reset_body(email, token)

        await self.arq_pool.enqueue_job(
            'send_email_async',
            to=email,
            subject="Reset your password for SmartBudget",
            body=email_body,
        )

        await self.arq_pool.enqueue_job(
            'send_kafka_event_async',
            topic="auth_events",
            event_data={"event": "user.password_reset_started", "email": email},
            schema_name="AUTH_EVENTS_SCHEMA"
        )

    async def complete_password_reset(self, body: schemas.CompleteResetRequest):
        """Завершает сброс пароля: проверяет токен и обновляет хэш пароля."""
        await self.validate_password_reset_token(body.token, body.email)
        redis_key = redis_keys.get_reset_password_key(body.email)

        user = await self.user_repo.get_by_email(body.email)
        if not user:
            raise exceptions.UserNotFoundError("User not found")

        await self.user_repo.update_password(user, utils.hash_password(body.new_password))
        await self.redis.delete(redis_key)

        await self.session_repo.revoke_all_for_user(user.id)

        await self.arq_pool.enqueue_job(
            'send_kafka_event_async',
            topic="auth_events",
            event_data = {
                "event": "user.password_reset",
                "user_id": str(user.id),
                "email": user.email,
            },
            schema_name="AUTH_EVENTS_SCHEMA"
        )

    async def change_password(self, user_id: str, body: schemas.ChangePasswordRequest):
        """Изменяет пароль пользователя, используя user_id из токена."""
        user = await self.user_repo.get_by_id(UUID(user_id))
        if not user or not utils.check_password(body.password, user.password_hash):
            raise exceptions.InvalidCredentialsError("Invalid current password")

        pw_hash = utils.hash_password(body.new_password)
        await self.user_repo.update_password(user, pw_hash)
        await self.session_repo.revoke_all_for_user(user.id)

        await self.arq_pool.enqueue_job(
            'send_kafka_event_async',
            topic="auth_events",
            event_data={"event": "user.password_changed", "user_id": user_id},
            schema_name="AUTH_EVENTS_SCHEMA"
        )

    async def get_user_info_by_id(self, user_id: str):
        """Получает пользователя по ID (для эндпоинта /me)."""
        user = await self.user_repo.get_by_id(UUID(user_id))
        if not user or not user.is_active:
            raise exceptions.UserInactiveError("User not found or inactive")
        return user

    async def get_all_sessions(
        self, 
        user_id: str, 
        current_refresh_token: str | None
    ) -> list[schemas.SessionInfo]:
        """Получает все активные сессии для пользователя и помечает, какая является текущей."""
        current_fingerprint = None
        if current_refresh_token:
            current_fingerprint = utils.hash_token(current_refresh_token)

        sessions = await self.session_repo.get_all_active(UUID(user_id))

        session_info_list = []
        for session in sessions:
            is_current = (session.refresh_fingerprint == current_fingerprint)
            session_info_list.append(
                schemas.SessionInfo(
                    id=session.id,
                    device_name=session.device_name,
                    location=session.location,
                    ip=session.ip,
                    created_at=session.created_at,
                    is_current_session=is_current
                )
            )
        return session_info_list

    async def revoke_session_by_id(self, user_id: str, session_id: str):
        """Отзывает одну конкретную сессию по ID. Проверка user_id для безопасности."""
        await self.session_repo.revoke_by_id(UUID(user_id), UUID(session_id))
        middleware.logger.info(f"Session {session_id} has been revoked by user {user_id}")

    async def revoke_other_sessions(self, user_id: str, current_refresh_token: str):
        """Отзывает все сессии пользователя, кроме текущей."""
        current_fingerprint = utils.hash_token(current_refresh_token)
        revoked_count = await self.session_repo.revoke_all_except(UUID(user_id), current_fingerprint)
        middleware.logger.info(f"Revoked {revoked_count} other sessions for user {user_id}")

    async def validate_access_token_async(self, token: str):
        """Валидирует access_token."""
        try:
            payload = decode(
                token, 
                settings.settings.jwt.jwt_public_key,
                algorithms=[settings.settings.jwt.jwt_algorithm],
                issuer="auth-service",
                audience="smart-budget",
            )
            user_id = payload.get("sub")
            if not user_id:
                raise exceptions.InvalidTokenError("Invalid token (missing sub)")

            user = await self.user_repo.get_by_id(UUID(user_id))
            if not user or not user.is_active:
                raise exceptions.UserInactiveError("User inactive or not found")
        except PyJWTError as e:
            raise exceptions.InvalidTokenError(f"Invalid token: {str(e)}")
        except ValueError:
            raise exceptions.InvalidTokenError("Invalid token payload (bad UUID)")


    async def refresh_session(self, refresh_token: str, access_token: str):
        """Обновляет сеанс с помощью проверки."""
        if not access_token:
            raise exceptions.InvalidTokenError("Missing access token")
        try:
            payload = decode(
                access_token,
                settings.settings.jwt.jwt_public_key,
                algorithms=[settings.settings.jwt.jwt_algorithm],
                audience="smart-budget",
                options={"verify_exp": False},
            )
            user_id = UUID(payload.get("sub"))
        except PyJWTError as e:
            raise exceptions.InvalidTokenError(f"Invalid access token: {str(e)}")
        except ValueError:
            raise exceptions.InvalidTokenError("Invalid access token payload (bad UUID)")


        fingerprint = utils.hash_token(refresh_token)
        session = await self.session_repo.get_by_fingerprint(user_id, fingerprint)
        if not session:
            raise exceptions.InvalidTokenError("Invalid or expired refresh token")
        
        role = await self.user_repo.get_role_by_id(user_id)
        
        new_access_token = self._create_access_token(str(user_id), role)
        new_refresh_token = str(uuid4())
        new_fingerprint = utils.hash_token(new_refresh_token)
        await self.session_repo.update_fingerprint(
            session, 
            new_fingerprint, 
            datetime.now(timezone.utc) + timedelta(days=30)
        )

        await self.arq_pool.enqueue_job(
            'send_kafka_event_async',
            topic="auth_events",
            event_data={"event": "user.token_refreshed", "user_id": str(user_id)},
            schema_name="AUTH_EVENTS_SCHEMA"
        )

        return new_access_token, new_refresh_token

    def _create_access_token(self, user_id: str, role: int) -> str:
        """Генерирует access_token."""
        access_payload = {
            "sub": user_id,
            "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
            "role": models.UserRole(role).name,
            "iss": "auth-service",
            "aud": "smart-budget"
        }
        return encode(
            access_payload, 
            settings.settings.jwt.jwt_private_key,
            algorithm=settings.settings.jwt.jwt_algorithm
        )   
    
    async def _create_session_and_tokens(
        self, 
        user: models.User, 
        user_agent: str | None,
        device_name: str, 
        ip: str, 
        location: str,
        commit: bool = True
    ):
        """Создает новый сеанс и генерирует токены."""
        refresh_token = str(uuid4())
        fingerprint = utils.hash_token(refresh_token)

        session_model = models.Session(
            id=uuid4(),
            user_id=user.id,
            user_agent=user_agent or "Unknown",
            device_name=device_name,
            ip=ip,
            location=location,
            revoked=False,
            refresh_fingerprint=fingerprint,
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            created_at=datetime.now(timezone.utc)
        )
        session = await self.session_repo.create(session_model)
        
        access_token = self._create_access_token(str(user.id), user.role)
        
        return access_token, refresh_token, session