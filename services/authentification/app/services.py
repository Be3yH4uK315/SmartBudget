from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from redis.asyncio import Redis
from uuid import uuid4
from datetime import datetime, timedelta, timezone
from jwt import encode, decode, PyJWTError
from hashlib import sha256
import sqlalchemy as sa

from app.dependencies import get_db, get_redis, get_arq_pool
from arq.connections import ArqRedis
from app.schemas import (
    CompleteRegistrationRequest, LoginRequest, 
    CompleteResetRequest, ChangePasswordRequest
)
from app.models import User, Session, UserRole
from app.utils import parse_device, get_location, hash_token, hash_password, check_password
from app.settings import settings
from app import constants

class AuthService:
    """
    Сервис, инкапсулирующий всю бизнес-логику аутентификации.
    """
    def __init__(
        self,
        db: AsyncSession = Depends(get_db),
        redis: Redis = Depends(get_redis),
        arq_pool: ArqRedis = Depends(get_arq_pool)
    ):
        self.db = db
        self.redis = redis
        self.arq_pool = arq_pool

    async def start_email_verification(self, email: str):
        """
        Проверяет, свободен ли email, и инициирует отправку
        письма с токеном верификации.
        """
        existing_user = await self.db.execute(select(User).where(User.email == email)) # type: ignore
        if existing_user.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Email already registered")

        token = str(uuid4())
        hashed_token = hash_token(token)
        redis_key = constants.get_verify_email_key(email)
        await self.redis.set(redis_key, hashed_token, ex=900)  # 15 мин TTL

        await self.arq_pool.enqueue_job(
            'send_email_async',
            to=email,
            subject="Verify your email for Budget App",
            body=f"Your verification token: {token}. Use it to complete registration."
        )

    async def validate_verification_token(self, token: str, email: str):
        """
        Проверяет валидность токена верификации из email.
        """
        hashed_token = hash_token(token)
        redis_key = constants.get_verify_email_key(email)
        stored_hash = await self.redis.get(redis_key)
        if not stored_hash or stored_hash != hashed_token:
            raise HTTPException(status_code=403, detail="Invalid or expired token")

    async def complete_registration(
        self, body: CompleteRegistrationRequest, ip: str
    ):
        """
        Завершает регистрацию: проверяет токен, создает
        User, Session и возвращает JWT токены.
        """
        hashed_token = hash_token(body.token)
        redis_key = constants.get_verify_email_key(body.email)
        stored = await self.redis.get(redis_key)
        if not stored or stored != hashed_token:
            raise HTTPException(status_code=403, detail="Invalid or expired token")
        await self.redis.delete(redis_key)

        device_name = parse_device(body.user_agent)
        location = get_location(ip)
        pw_hash = hash_password(body.password)

        user = User(
            id=uuid4(),
            role=UserRole.USER,
            email=body.email,
            password_hash=pw_hash,
            name=body.name,
            country=body.country,
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        self.db.add(user)
        try:
            await self.db.commit()
            await self.db.refresh(user)
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(status_code=409, detail="Email already registered")

        # Создаем сессию и токены
        access_token, refresh_token, session = await self._create_session_and_tokens(
            user=user,
            user_agent=body.user_agent,
            device_name=device_name,
            ip=ip,
            location=location
        )

        # Отправка событий Kafka
        event = {
            "event": "user.registered",
            "user_id": str(user.id),
            "email": body.email,
            "ip": ip,
            "location": location
        }
        # Ставим задачу в очередь Arq
        await self.arq_pool.enqueue_job(
            'send_kafka_event_async', 
            "budget.auth.events", 
            event, 
            "AUTH_EVENTS_SCHEMA"
        )

        user_event = {
            "user_id": str(user.id),
            "email": body.email,
            "name": body.name,
            "country": body.country,
            "role": user.role,
            "is_active": True
        }
        # Ставим задачу в очередь Arq
        await self.arq_pool.enqueue_job(
            'send_kafka_event_async', 
            "users.active", 
            user_event, 
            "USERS_ACTIVE_SCHEMA"
        )
        
        return user, session, access_token, refresh_token

    async def authenticate_user(
        self, body: LoginRequest, ip: str
    ):
        """
        Аутентифицирует пользователя: проверяет email/пароль,
        отслеживает неудачи, создает Session и возвращает JWT.
        """
        fail_key = constants.get_login_fail_key(ip)
        fails = int(await self.redis.get(fail_key) or 0)
        if fails >= 5:
            raise HTTPException(status_code=429, detail="Too many attempts, try later")

        user_query = await self.db.execute(select(User).where(User.email == body.email, User.is_active == sa.true())) # type: ignore
        user = user_query.scalar_one_or_none()
        
        if not user or not check_password(body.password, user.password_hash):
            await self.redis.incr(fail_key)
            await self.redis.expire(fail_key, 300)  # 5 min lock
            raise HTTPException(status_code=403, detail="Invalid credentials")

        await self.redis.delete(fail_key)

        device_name = parse_device(body.user_agent)
        location = get_location(ip)

        # Создаем сессию и токены
        access_token, refresh_token, session = await self._create_session_and_tokens(
            user=user,
            user_agent=body.user_agent,
            device_name=device_name,
            ip=ip,
            location=location
        )
        
        user.last_login = datetime.now(timezone.utc)
        await self.db.commit()

        event = {"event": "user.login", "user_id": str(user.id), "ip": ip, "location": location}
        # Ставим задачу в очередь Arq
        await self.arq_pool.enqueue_job(
            'send_kafka_event_async', 
            "budget.auth.events", 
            event, 
            "AUTH_EVENTS_SCHEMA"
        )

        return user, session, access_token, refresh_token

    async def logout(self, refresh_token: str):
        """
        Производит выход из системы, отзывая сессию по refresh_token.
        """
        if not refresh_token:
            raise HTTPException(status_code=401, detail="Not authenticated")

        fingerprint = sha256(refresh_token.encode()).hexdigest()
        session_query = await self.db.execute(select(Session).where(
            Session.refresh_fingerprint == fingerprint, 
            Session.revoked == sa.false()
        ))
        session = session_query.scalar_one_or_none()

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session.revoked = True
        user_id_for_event = session.user_id
        await self.db.commit()
        
        event = {"event": "user.logout", "user_id": str(user_id_for_event)}
        await self.arq_pool.enqueue_job(
            'send_kafka_event_async', 
            "budget.auth.events", 
            event, 
            "AUTH_EVENTS_SCHEMA"
        )

    async def start_password_reset(self, email: str):
        """
        Инициирует сброс пароля, если пользователь существует.
        """
        user_query = await self.db.execute(select(User).where(User.email == email)) # type: ignore
        user = user_query.scalar_one_or_none()
        if not user:
            return

        token = str(uuid4())
        hashed_token = hash_token(token)
        redis_key = constants.get_reset_password_key(email)
        await self.redis.set(redis_key, hashed_token, ex=900)

        await self.arq_pool.enqueue_job(
            'send_email_async',
            to=email,
            subject="Reset your password",
            body=f"Your reset token: {token}"
        )

    async def complete_password_reset(self, body: CompleteResetRequest):
        """
        Завершает сброс пароля: проверяет токен и обновляет хэш пароля.
        """
        hashed_token = hash_token(body.token)
        redis_key = constants.get_reset_password_key(body.email)
        stored = await self.redis.get(redis_key)
        if not stored or stored != hashed_token:
            raise HTTPException(status_code=403, detail="Invalid token")
        await self.redis.delete(redis_key)

        pw_hash = hash_password(body.new_password)

        user_query = await self.db.execute(select(User).where(User.email == body.email)) # type: ignore
        user = user_query.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user.password_hash = pw_hash
        await self.db.commit()

        event = {"event": "user.password_reset", "user_id": str(user.id)}
        await self.arq_pool.enqueue_job(
            'send_kafka_event_async', 
            "budget.auth.events", 
            event, 
            "AUTH_EVENTS_SCHEMA"
        )

    async def change_password(self, body: ChangePasswordRequest):
        """
        Изменяет пароль пользователя после проверки текущего пароля.
        """
        user_query = await self.db.execute(select(User).where(User.id == body.user_id)) # type: ignore
        user = user_query.scalar_one_or_none()
        if not user or not check_password(body.password, user.password_hash):
            raise HTTPException(status_code=403, detail="Invalid current password")

        pw_hash = hash_password(body.new_password)
        user.password_hash = pw_hash
        await self.db.commit()

        event = {"event": "user.password_changed", "user_id": str(body.user_id)}
        await self.arq_pool.enqueue_job(
            'send_kafka_event_async', 
            "budget.auth.events", 
            event, 
            "AUTH_EVENTS_SCHEMA"
        )

    async def validate_access_token_async(self, token: str):
        """
        Валидирует access_token. Вызывается из /validate-token.
        """
        try:
            payload = decode(
                token, 
                settings.jwt_public_key,
                algorithms=[settings.jwt_algorithm]
            )
            if "sub" not in payload:
                raise PyJWTError("Missing sub")
        except PyJWTError:
            event = {"event": "user.token_invalid", "token": "anonymized"}
            await self.arq_pool.enqueue_job(
                'send_kafka_event_async', 
                "budget.auth.events", 
                event, 
                "AUTH_EVENTS_SCHEMA"
            )
            raise HTTPException(status_code=401, detail="Invalid token")

    async def refresh_session(
        self, refresh_token: str, access_token: str
    ) -> str:
        """
        Обновляет access_token, используя refresh_token.
        """
        if not access_token:
            raise HTTPException(status_code=401, detail="Missing access token")

        try:
            # Декодируем access_token без проверки exp, чтобы получить user_id
            payload = decode(access_token, settings.jwt_public_key, algorithms=[settings.jwt_algorithm], options={"verify_exp": False})
            user_id = payload.get("sub")
            if not user_id:
                raise PyJWTError("Missing sub")
        except PyJWTError as e:
            raise HTTPException(status_code=401, detail="Invalid access token")

        fingerprint = sha256(refresh_token.encode()).hexdigest()
        session_query = await self.db.execute(select(Session).where(
            Session.user_id == user_id, # type: ignore
            Session.refresh_fingerprint == fingerprint, # type: ignore
            Session.revoked == sa.false(),# type: ignore
            Session.expires_at > datetime.now(timezone.utc)
        ))
        session = session_query.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=403, detail="Invalid refresh token")

        # Получаем роль пользователя для нового токена
        role_result = await self.db.execute(select(User.role).where(User.id == user_id)) # type: ignore
        role = role_result.scalar()
        
        # Создаем только новый access_token
        new_access_token = self._create_access_token(user_id=str(user_id), role=role or UserRole.USER)
        return new_access_token

    # --- Приватные методы ---

    def _create_access_token(self, user_id: str, role: int) -> str:
        """Генерирует access_token."""
        access_payload = {
            "sub": user_id,
            "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
            "role": role
        }
        return encode(
            access_payload, 
            settings.jwt_private_key,
            algorithm=settings.jwt_algorithm
        )
    
    async def _create_session_and_tokens(
        self, user: User, user_agent: str, device_name: str, ip: str, location: str
    ):
        """
        Создает новую сессию в БД, генерирует access и refresh токены.
        """
        refresh_token = str(uuid4())
        fingerprint = sha256(refresh_token.encode()).hexdigest()

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
        
        # Коммит сессии
        await self.db.commit() 
        
        return access_token, refresh_token, session
