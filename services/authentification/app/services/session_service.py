import logging
from uuid import UUID, uuid4
from datetime import timedelta
from typing import Optional

import orjson
from redis.asyncio import Redis
from redis.exceptions import LockError

from app.core import exceptions, config
from app.infrastructure.db import models, uow
from app.domain.schemas import dtos
from app.domain.mappers.user import user_to_dto
from app.domain.mappers.session import session_to_dto
from app.utils import redis_keys, crypto, time
from app.services.token_service import TokenService
from app.services.notifier import AuthNotifier

logger = logging.getLogger(__name__)
settings = config.settings

class SessionService:
    """Сервис управления сессиями."""

    def __init__(
        self,
        uow: uow.UnitOfWork,
        redis: Redis,
        token_service: TokenService,
        notifier: AuthNotifier,
    ):
        self.uow = uow
        self.redis = redis
        self.token_service = token_service
        self.notifier = notifier

    async def _cache_session_data(
        self,
        session_dto: dtos.SessionDTO,
        user_dto: dtos.UserDTO,
    ) -> None:
        """Кэширует минимальные данные сессии."""
        data = {
            "uid": str(user_dto.user_id),
            "role": user_dto.role.value,
            "exp": session_dto.expires_at.timestamp() 
        }
        key = redis_keys.get_session_key(str(session_dto.session_id))

        await self.redis.set(
            key,
            orjson.dumps(data),
            ex=int(timedelta(days=settings.JWT.SESSION_CACHE_EXPIRE_DAYS).total_seconds()),
        )

    async def cache_user_data(self, user_dto: dtos.UserDTO) -> None:
        """Кэширует полного пользователя."""
        cache_key = redis_keys.get_user_cache_key(str(user_dto.user_id))
        await self.redis.set(
            cache_key,
            user_dto.model_dump_json(),
            ex=600,
        )

    async def invalidate_user_cache(self, user_id: UUID) -> None:
        await self.redis.delete(
            redis_keys.get_user_cache_key(str(user_id))
        )

    async def clear_session_cache(self, session_id: UUID) -> None:
        await self.redis.delete(
            redis_keys.get_session_key(str(session_id))
        )

    async def clear_sessions_cache_bulk(
        self,
        session_ids: list[UUID],
    ) -> None:
        """Массовая очистка кэша сессий."""
        if not session_ids:
            return

        keys = [
            redis_keys.get_session_key(str(sid))
            for sid in session_ids
        ]
        await self.redis.delete(*keys)

    async def activate_session_in_cache(
        self,
        session_dto: dtos.SessionDTO,
        user_dto: dtos.UserDTO,
    ) -> None:
        """Активирует кэш после успешного commit."""
        session_key = redis_keys.get_session_key(str(session_dto.session_id))
        session_data = {
            "uid": str(user_dto.user_id),
            "role": user_dto.role.value,
            "exp": session_dto.expires_at.timestamp()
        }
        
        user_key = redis_keys.get_user_cache_key(str(user_dto.user_id))

        async with self.redis.pipeline(transaction=True) as pipe:
            await pipe.set(
                session_key,
                orjson.dumps(session_data),
                ex=int(timedelta(days=settings.JWT.SESSION_CACHE_EXPIRE_DAYS).total_seconds())
            )
            await pipe.set(
                user_key,
                user_dto.model_dump_json(),
                ex=600
            )
            await pipe.execute()

    async def create_session_and_tokens(
        self,
        user: models.User,
        user_agent: str,
        device_name: str,
        ip: str,
        location: str,
    ) -> tuple[str, str, models.Session]:
        """Создаёт ORM-сессию и токены."""
        refresh_token = str(uuid4())
        fingerprint = crypto.hash_token(refresh_token)
        now = time.utc_now()
        retention = user.retention_days if user.retention_days else 30

        session = models.Session(
            session_id=uuid4(),
            user_id=user.user_id,
            user_agent=user_agent,
            device_name=device_name,
            ip=ip,
            location=location,
            revoked=False,
            refresh_fingerprint=fingerprint,
            last_activity=now,
            expires_at=now + timedelta(days=retention),
            created_at=now,
        )

        self.uow.sessions.create(session)

        access_token = self.token_service.create_access_token(
            str(user.user_id),
            user.role,
            str(session.session_id),
        )

        return access_token, refresh_token, session

    async def refresh_session(self, refresh_token: str) -> tuple[str, str]:
        """Обновление refresh/access токенов."""
        fingerprint = crypto.hash_token(refresh_token)
        lock_key = f"auth:lock:refresh:{fingerprint}"

        try:
            async with self.redis.lock(
                lock_key,
                timeout=5,
                blocking_timeout=2,
            ):
                async with self.uow:
                    session = await self.uow.sessions.get_by_fingerprint(
                        fingerprint
                    )
                    if not session:
                        raise exceptions.InvalidTokenError(
                            "Invalid refresh token"
                        )

                    if session.expires_at < time.utc_now():
                        session.revoked = True
                        await self.uow.commit()
                        
                        await self.clear_session_cache(session.session_id)
                        
                        raise exceptions.InvalidTokenError("Refresh token expired")

                    user_orm = await self.uow.users.get_by_id(
                        session.user_id
                    )
                    if not user_orm:
                        raise exceptions.UserNotFoundError(
                            "User not found"
                        )

                    retention = user_orm.retention_days
                    new_refresh = str(uuid4())
                    new_fingerprint = crypto.hash_token(new_refresh)
                    new_expires = time.utc_now() + timedelta(days=retention)

                    await self.uow.sessions.update_fingerprint(
                        session,
                        new_fingerprint,
                        new_expires,
                    )

                    new_access = self.token_service.create_access_token(
                        str(user_orm.user_id),
                        user_orm.role,
                        str(session.session_id),
                    )

                    await self.notifier.notify_token_refreshed(
                        str(user_orm.user_id)
                    )

                    session_dto = session_to_dto(session)
                    session_dto.is_current = True
                    user_dto = user_to_dto(user_orm)

                    await self.uow.commit()

                await self.activate_session_in_cache(
                    session_dto,
                    user_dto,
                )

                return new_access, new_refresh

        except LockError:
            raise exceptions.TooManyAttemptsError(
                "Refresh already in progress"
            )

    async def validate_access_token(self, token: str) -> None:
        payload = self.token_service.get_token_payload(token)
        session_id = payload.get("sid")
        cache_key = redis_keys.get_session_key(session_id)

        session_json = await self.redis.get(cache_key)

        if session_json:
            try:
                data = orjson.loads(session_json)
                exp_timestamp = data.get("exp")
                if exp_timestamp and time.utc_timestamp() < exp_timestamp:
                    return
            except Exception:
                pass

        async with self.uow:
            session = await self.uow.sessions.get_active_by_id(
                UUID(session_id)
            )
            if not session:
                raise exceptions.InvalidTokenError(
                    "Revoked or expired"
                )

            user_orm = await self.uow.users.get_by_id(
                session.user_id
            )
            if not user_orm:
                raise exceptions.UserNotFoundError()

            session_dto = session_to_dto(session)
            user_dto = user_to_dto(user_orm)

        await self.activate_session_in_cache(
            session_dto,
            user_dto,
        )

    async def get_all_sessions(
        self,
        user_id: UUID,
        current_refresh_token: str | None,
    ) -> list[dtos.SessionDTO]:
        current_fp = (
            crypto.hash_token(current_refresh_token)
            if current_refresh_token
            else None
        )

        async with self.uow:
            sessions = await self.uow.sessions.get_all_active(
                user_id
            )

        result: list[dtos.SessionDTO] = []
        current_session_dto: dtos.SessionDTO | None = None
        for s in sessions:
            dto = session_to_dto(s)
            if current_fp and s.refresh_fingerprint == current_fp:
                dto.is_current = True
                current_session_dto = dto
            
            result.append(dto)
        if current_session_dto:
            result.remove(current_session_dto)
            result.insert(0, current_session_dto)

        return result
    
    async def revoke_session(
        self,
        user_id: UUID,
        session_id: UUID,
    ) -> None:
        async with self.uow:
            await self.uow.sessions.revoke_by_id(
                user_id,
                session_id,
            )
            await self.notifier.notify_session_revoked(
                str(user_id),
                str(session_id),
            )
            await self.uow.commit()

        await self.clear_session_cache(session_id)

    async def revoke_other_sessions(
        self,
        user_id: UUID,
        current_refresh_token: str,
    ) -> None:
        current_fp = crypto.hash_token(current_refresh_token)

        async with self.uow:
            revoked_ids = await self.uow.sessions.revoke_all_except(
                user_id,
                current_fp,
            )
            await self.uow.commit()

        if revoked_ids:
            await self.clear_sessions_cache_bulk(revoked_ids)

    async def revoke_all_user_sessions(
        self,
        user_id: UUID,
    ) -> None:
        async with self.uow:
            revoked_ids = await self.uow.sessions.revoke_all_for_user(
                user_id
            )
            await self.uow.commit()

        if revoked_ids:
            await self.clear_sessions_cache_bulk(revoked_ids)

    async def get_user_and_session_id(
        self,
        token: str,
    ) -> tuple[dtos.UserDTO, str]:
        payload = self.token_service.get_token_payload(token)
        user_id = payload.get("sub")
        session_id = payload.get("sid")

        session_cache_key = redis_keys.get_session_key(session_id)
        session_json_raw = await self.redis.get(session_cache_key)

        is_session_valid = False

        if session_json_raw:
            try:
                session_data = orjson.loads(session_json_raw)
                exp_timestamp = session_data.get("exp")
                if exp_timestamp and time.utc_timestamp() > exp_timestamp:
                    await self.redis.delete(session_cache_key)
                    is_session_valid = False
                else:
                    is_session_valid = True
            except Exception:
                await self.redis.delete(session_cache_key)
                is_session_valid = False

        if not is_session_valid:
            async with self.uow:
                session_orm = await self.uow.sessions.get_active_by_id(UUID(session_id))
                
                if not session_orm:
                    raise exceptions.InvalidTokenError("Session revoked or expired")
                
                user_orm = await self.uow.users.get_by_id(UUID(user_id))
                if not user_orm:
                     raise exceptions.UserNotFoundError()

                session_dto = session_to_dto(session_orm)
                user_dto = user_to_dto(user_orm)
            
            await self.activate_session_in_cache(session_dto, user_dto)
            
            if not user_dto.is_active:
                raise exceptions.UserInactiveError()
            
            return user_dto, session_id
        
        cache_key = redis_keys.get_user_cache_key(user_id)
        cached_user = await self.redis.get(cache_key)

        user_dto: Optional[dtos.UserDTO] = None
        if cached_user:
            try:
                user_dto = dtos.UserDTO.model_validate_json(cached_user)
            except Exception:
                logger.warning(f"Failed to parse cached user {user_id}")

        if not user_dto:
            async with self.uow:
                user_orm = await self.uow.users.get_by_id(UUID(user_id))
                if not user_orm:
                    raise exceptions.UserNotFoundError()

            user_dto = user_to_dto(user_orm)
            await self.cache_user_data(user_dto)

        if not user_dto.is_active:
            raise exceptions.UserInactiveError()

        return user_dto, session_id
    
    async def update_activity(self, session_id: UUID) -> None:
        throttle_key = f"auth:session:activity:{session_id}"

        should_update = await self.redis.set(
            throttle_key,
            "1",
            ex=300,
            nx=True,
        )

        if should_update:
            async with self.uow:
                await self.uow.sessions.update_last_activity(
                    session_id,
                    time.utc_now(),
                )
                await self.uow.commit()
    
    async def update_user_retention_settings(self, user_id: UUID, days: int) -> None:
        async with self.uow:
            await self.uow.users.update_retention_days(user_id, days)
            await self.uow.commit()
        
        await self.invalidate_user_cache(user_id)
    
    async def verify_session_fast(self, session_id: str) -> bool:
        """Быстрая проверка сессии только через кэш."""
        session_key = redis_keys.get_session_key(session_id)
        cached_raw = await self.redis.get(session_key)
        
        if not cached_raw:
            return False

        try:
            session_data = orjson.loads(cached_raw)
            exp_timestamp = session_data.get("exp")
            
            if exp_timestamp and time.utc_timestamp() > exp_timestamp:
                return False
                
            return True
        except Exception:
            return False