import asyncio
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from redis.asyncio import Redis
from uuid import uuid4, UUID
from datetime import datetime, timedelta, timezone
from jwt import encode, decode, PyJWTError
import sqlalchemy as sa
import geoip2.database
from arq.connections import ArqRedis

from .email_templates import get_password_reset_body, get_verification_email_body
from .middleware import logger
from .dependencies import get_db, get_redis, get_arq_pool, get_geoip_reader
from .schemas import (
    CompleteRegistrationRequest, LoginRequest, 
    CompleteResetRequest, ChangePasswordRequest
)
from .models import User, Session, UserRole
from .utils import parse_device, get_location, hash_token, hash_password, check_password
from .settings import settings
from app import constants

class AuthService:
    """Сервис, инкапсулирующий всю бизнес-логику аутентификации."""
    def __init__(
        self,
        db: AsyncSession = Depends(get_db),
        redis: Redis = Depends(get_redis),
        arq_pool: ArqRedis = Depends(get_arq_pool),
        geoip_reader: geoip2.database.Reader = Depends(get_geoip_reader)
    ):
        self.db = db
        self.redis = redis
        self.arq_pool = arq_pool
        self.geoip_reader = geoip_reader

    async def start_email_verification(self, email: str):
        """Проверяет, свободен ли email, и инициирует отправку письма с токеном верификации."""
        existing_user = await self.db.execute(select(User).where(User.email == email)) 
        if existing_user.scalar_one_or_none():
            logger.warning(f"Verification attempt for existing email: {email}")
            return "sign_in"

        token = str(uuid4())
        hashed_token = hash_token(token)
        redis_key = constants.get_verify_email_key(email)
        await self.redis.set(redis_key, hashed_token, ex=900)  # 15 мин TTL

        email_body = get_verification_email_body(email, token)
        
        logger.info(f"Arq pool in AuthService: {self.arq_pool}")
        logger.info(f"Enqueueing send_email_async to {email} in queue {settings.arq_queue_name}")
        job = await self.arq_pool.enqueue_job(
            'send_email_async',
            to=email,
            subject="Verify your email for SmartBudget",
            body=email_body,
        )
        logger.info(f"Job enqueued: {job.job_id}")

        await self.arq_pool.enqueue_job(
            'send_kafka_event_async',
            topic="auth_events",
            event_data={"event": "user.verification_started", "email": email},
            schema_name="AUTH_EVENTS_SCHEMA"
        )
        return "sign_up"

    async def validate_verification_token(self, token: str, email: str):
        """Проверяет валидность токена верификации из email."""
        redis_key = constants.get_verify_email_key(email)
        stored_hash = await self.redis.get(redis_key)
        if not stored_hash or stored_hash != hash_token(token):
            raise HTTPException(status_code=403, detail="Invalid or expired token")

        await self.arq_pool.enqueue_job(
            'send_kafka_event_async',
            topic="auth_events",
            event_data={"event": "user.verification_validated", "email": email},
            schema_name="AUTH_EVENTS_SCHEMA"
        )

    async def complete_registration(self, body: CompleteRegistrationRequest, ip: str):
        """Завершает регистрацию: создает пользователя и сеанс."""
        await self.validate_verification_token(body.token, body.email)
        redis_key = constants.get_verify_email_key(body.email)
        try:
            user = User(
                id=uuid4(),
                email=body.email,
                name=body.name,
                country=body.country,
                password_hash=hash_password(body.password),
                is_active=True,
                role=UserRole.USER.value
            )
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)

            device_name = parse_device(body.user_agent)
            location = await asyncio.to_thread(get_location, ip, self.geoip_reader)

            access_token, refresh_token, session = await self._create_session_and_tokens(
                user, body.user_agent, device_name, ip, location
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
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(status_code=409, detail="Email already registered")

    async def authenticate_user(
        self, body: LoginRequest, ip: str
    ):
        """Выполняет вход в систему: проверяет учетные данные и создает сеанс."""
        fail_key = constants.get_login_fail_key(ip)
        fails = int(await self.redis.get(fail_key) or 0)
        if fails >= 5:
            raise HTTPException(status_code=429, detail="Too many attempts, try later")

        location = await asyncio.to_thread(get_location, ip, self.geoip_reader)

        user_query = await self.db.execute(
            select(User).where(
                User.email == body.email,
                User.is_active == sa.true(),
            )
        )
        user = user_query.scalar_one_or_none()
        if not user or not check_password(body.password, user.password_hash):
            await self.redis.incr(fail_key)
            await self.redis.expire(fail_key, 60)  # 5 min lock
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
            raise HTTPException(status_code=403, detail="Invalid credentials")

        await self.redis.delete(fail_key)

        device_name = parse_device(body.user_agent)

        user.last_login = datetime.now(timezone.utc)
        self.db.add(user)

        access_token, refresh_token, session = await self._create_session_and_tokens(
            user, body.user_agent, device_name, ip, location
        )

        await self.db.execute(
            update(User)
            .where(User.id == user.id)
            .values(
                last_login=datetime.now(timezone.utc),
            )
        )
        await self.db.commit()

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
            raise HTTPException(status_code=401, detail="Not authenticated")

        fingerprint = hash_token(refresh_token)
        await self.db.execute(update(Session).where(
            Session.user_id == UUID(user_id),
            Session.refresh_fingerprint == fingerprint
        ).values(revoked=True))
        await self.db.commit()

        await self.arq_pool.enqueue_job(
            'send_kafka_event_async',
            topic="auth_events",
            event_data={"event": "user.logout", "user_id": user_id},
            schema_name="AUTH_EVENTS_SCHEMA"
        )

    async def start_password_reset(self, email: str):
        """Инициирует сброс пароля, если пользователь существует."""
        user_query = await self.db.execute(select(User).where(User.email == email)) 
        user = user_query.scalar_one_or_none()
        if not user:
            logger.warning(f"Password reset attempt for non-existing email: {email}")
            return

        token = str(uuid4())
        hashed_token = hash_token(token)
        redis_key = constants.get_reset_password_key(email)
        await self.redis.set(redis_key, hashed_token, ex=900) # 15 min TTL
        
        email_body = get_password_reset_body(email, token)

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

    async def complete_password_reset(self, body: CompleteResetRequest):
        """Завершает сброс пароля: проверяет токен и обновляет хэш пароля."""
        redis_key = constants.get_reset_password_key(body.email)
        stored_hash = await self.redis.get(redis_key)
        if not stored_hash or hash_token(body.token) != stored_hash:
            raise HTTPException(status_code=400, detail="Invalid or expired token")

        user_query = await self.db.execute(select(User).where(User.email == body.email))
        user = user_query.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user.password_hash = hash_password(body.new_password)
        await self.db.commit()
        await self.redis.delete(redis_key)

        await self.db.execute(
            update(Session)
            .where(Session.user_id == user.id)
            .values(revoked=True)
        )
        await self.db.commit()

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

    async def change_password(self, user_id: str, body: ChangePasswordRequest):
        """Изменяет пароль пользователя, используя user_id из токена."""
        user_query = await self.db.execute(select(User).where(User.id == UUID(user_id)))
        user = user_query.scalar_one_or_none()
        if not user or not check_password(body.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid current password")

        pw_hash = hash_password(body.new_password)
        user.password_hash = pw_hash
        await self.db.execute(
            update(Session)
            .where(Session.user_id == user.id, Session.revoked == sa.false())
            .values(revoked=True)
        )
        await self.db.commit()

        await self.arq_pool.enqueue_job(
            'send_kafka_event_async',
            topic="auth_events",
            event_data={"event": "user.password_changed", "user_id": user_id},
            schema_name="AUTH_EVENTS_SCHEMA"
        )

    async def validate_access_token_async(self, token: str):
        """Валидирует access_token."""
        try:
            payload = decode(
                token, 
                settings.jwt_public_key,
                algorithms=[settings.jwt_algorithm],
                issuer="auth-service",
                audience="smart-budget",
            )
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(status_code=401, detail="Invalid token")

            user = await self.db.get(User, UUID(user_id))
            if not user or not user.is_active:
                raise HTTPException(status_code=401, detail="User inactive")
        except PyJWTError as e:
            raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

    async def refresh_session(self, refresh_token: str, access_token: str):
        """Обновляет сеанс с помощью проверки."""
        if not access_token:
            raise HTTPException(status_code=401, detail="Missing access token")
        try:
            payload = decode(
                access_token,
                settings.jwt_public_key,
                algorithms=[settings.jwt_algorithm],
                audience="smart-budget",
                options={"verify_exp": False},
            )
            user_id = UUID(payload.get("sub"))
        except PyJWTError as e:
            raise HTTPException(status_code=401, detail=f"Invalid access token: {str(e)}")

        fingerprint = hash_token(refresh_token)
        session_query = await self.db.execute(select(Session).where(
            Session.user_id == user_id,
            Session.refresh_fingerprint == fingerprint,
            Session.revoked == sa.false(),
            Session.expires_at > datetime.now(timezone.utc)
        ))
        session = session_query.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=403, detail="Invalid refresh token")
        
        role_result = await self.db.execute(select(User.role).where(User.id == user_id))
        role = role_result.scalar() or UserRole.USER.value
        
        new_access_token = self._create_access_token(str(user_id), role)
        new_refresh_token = str(uuid4())
        new_fingerprint = hash_token(new_refresh_token)
        session.refresh_fingerprint = new_fingerprint
        session.expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        await self.db.commit()

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
            "role": UserRole(role).name,
            "iss": "auth-service",
            "aud": "smart-budget"
        }
        return encode(
        access_payload, 
        settings.jwt_private_key,
        algorithm=settings.jwt_algorithm
        )   
    
    async def _create_session_and_tokens(
        self, user: User, user_agent: str, device_name: str, ip: str, location: str,
        commit: bool = True
    ):
        """Создает новый сеанс и генерирует токены."""
        refresh_token = str(uuid4())
        fingerprint = hash_token(refresh_token)

        session = Session(
            id=uuid4(),
            user_id=user.id,
            user_agent=user_agent,
            device_name=device_name,
            ip=ip,
            location=location,
            revoked=False,
            refresh_fingerprint=fingerprint,
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            created_at=datetime.now(timezone.utc)
        )
        self.db.add(session)
        
        access_token = self._create_access_token(str(user.id), user.role)
        
        if commit:
            await self.db.commit()

        return access_token, refresh_token, session