import logging
from datetime import timedelta
from uuid import UUID, uuid4

import orjson
from redis.asyncio import Redis
from redis.exceptions import LockError

from app.core import config, exceptions
from app.domain.mappers.session import session_to_dto
from app.domain.mappers.user import user_to_dto
from app.domain.schemas import dtos
from app.infrastructure.db import models, uow
from app.services.notifier import AuthNotifier
from app.services.token_service import TokenService
from app.utils import crypto, redis_keys, time

logger = logging.getLogger(__name__)
settings = config.settings

DEFAULT_RETENTION_DAYS = 30
USER_CACHE_TTL_SECONDS = 600
ACTIVITY_THROTTLE_SECONDS = 300
REFRESH_LOCK_TIMEOUT_SECONDS = 5
REFRESH_LOCK_BLOCKING_TIMEOUT_SECONDS = 2


class SessionService:
    """Сервис управления пользовательскими сессиями."""

    def __init__(
        self,
        uow: uow.UnitOfWork,
        redis: Redis,
        token_service: TokenService,
        notifier: AuthNotifier,
    ) -> None:
        self.uow = uow
        self.redis = redis
        self.token_service = token_service
        self.notifier = notifier

    async def cache_user_data(self, user_dto: dtos.UserDTO) -> None:
        """Кэширует данные пользователя."""
        await self.redis.set(
            redis_keys.get_user_cache_key(str(user_dto.user_id)),
            user_dto.model_dump_json(),
            ex=USER_CACHE_TTL_SECONDS,
        )

    async def invalidate_user_cache(self, user_id: UUID) -> None:
        """Удаляет кэш пользователя."""
        await self.redis.delete(redis_keys.get_user_cache_key(str(user_id)))

    async def clear_session_cache(self, session_id: UUID) -> None:
        """Очищает кэш конкретной сессии."""
        await self.redis.delete(redis_keys.get_session_key(str(session_id)))

    async def clear_sessions_cache_bulk(self, session_ids: list[UUID]) -> None:
        """Очищает кэш нескольких сессий."""
        if not session_ids:
            return

        keys = [redis_keys.get_session_key(str(session_id)) for session_id in session_ids]
        await self.redis.delete(*keys)

    async def activate_session_in_cache(
        self,
        session_dto: dtos.SessionDTO,
        user_dto: dtos.UserDTO,
    ) -> None:
        """Кэширует сессию и пользователя после успешного commit."""
        session_key = redis_keys.get_session_key(str(session_dto.session_id))
        user_key = redis_keys.get_user_cache_key(str(user_dto.user_id))

        async with self.redis.pipeline(transaction=True) as pipe:
            await pipe.set(
                session_key,
                self._build_session_cache_payload(session_dto, user_dto),
                ex=self._session_cache_ttl_seconds,
            )
            await pipe.set(
                user_key,
                user_dto.model_dump_json(),
                ex=USER_CACHE_TTL_SECONDS,
            )
            await pipe.execute()

    async def create_session_and_tokens(
        self,
        user: models.User,
        user_agent: str,
        device_name: str,
        ip: str,
        location: str | None,
    ) -> tuple[str, str, models.Session]:
        """Создает ORM-сессию, access token и refresh token."""
        refresh_token = str(uuid4())
        refresh_fingerprint = crypto.hash_token(refresh_token)

        now = time.utc_now()
        retention_days = user.retention_days or DEFAULT_RETENTION_DAYS

        session = models.Session(
            session_id=uuid4(),
            user_id=user.user_id,
            user_agent=user_agent,
            device_name=device_name,
            ip=ip,
            location=location,
            revoked=False,
            refresh_fingerprint=refresh_fingerprint,
            last_activity=now,
            expires_at=now + timedelta(days=retention_days),
            created_at=now,
        )

        self.uow.sessions.create(session)

        access_token = self.token_service.create_access_token(
            user_id=str(user.user_id),
            role=user.role,
            session_id=str(session.session_id),
        )

        return access_token, refresh_token, session

    async def refresh_session(self, refresh_token: str) -> tuple[str, str]:
        """Обновляет access token и refresh token."""
        fingerprint = crypto.hash_token(refresh_token)
        lock_key = f"auth:lock:refresh:{fingerprint}"

        try:
            async with self.redis.lock(
                lock_key,
                timeout=REFRESH_LOCK_TIMEOUT_SECONDS,
                blocking_timeout=REFRESH_LOCK_BLOCKING_TIMEOUT_SECONDS,
            ):
                return await self._refresh_session_locked(fingerprint)

        except LockError as exc:
            raise exceptions.TooManyAttemptsError(
                "Refresh already in progress",
            ) from exc

    async def validate_access_token(self, token: str) -> None:
        """Проверяет access token и актуальность связанной сессии."""
        payload = await self.token_service.get_token_payload(token)
        session_id = self._get_required_payload_value(payload, "sid")

        session_key = redis_keys.get_session_key(session_id)
        session_cache = await self._get_valid_session_cache(session_key)

        if session_cache is not None:
            return

        async with self.uow:
            session = await self.uow.sessions.get_active_by_id(UUID(session_id))
            if not session:
                raise exceptions.InvalidTokenError("Revoked or expired")

            user = await self.uow.users.get_by_id(session.user_id)
            if not user:
                raise exceptions.UserNotFoundError("User not found")

            session_dto = session_to_dto(session)
            user_dto = user_to_dto(user)

        await self.activate_session_in_cache(session_dto, user_dto)

    async def get_all_sessions(
        self,
        user_id: UUID,
        current_refresh_token: str | None,
    ) -> list[dtos.SessionDTO]:
        """Получает все активные сессии пользователя."""
        current_fingerprint = (
            crypto.hash_token(current_refresh_token) if current_refresh_token else None
        )

        async with self.uow:
            sessions = await self.uow.sessions.get_all_active(user_id)

        session_dtos = [session_to_dto(session) for session in sessions]

        if not current_fingerprint:
            return session_dtos

        for index, session in enumerate(sessions):
            if session.refresh_fingerprint == current_fingerprint:
                current_session = session_dtos.pop(index)
                current_session.is_current = True
                session_dtos.insert(0, current_session)
                break

        return session_dtos

    async def revoke_session(
        self,
        user_id: UUID,
        session_id: UUID,
    ) -> None:
        """Отзывает конкретную сессию пользователя."""
        async with self.uow:
            await self.uow.sessions.revoke_by_id(user_id, session_id)
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
        """Отзывает все сессии пользователя, кроме текущей."""
        current_fingerprint = crypto.hash_token(current_refresh_token)

        async with self.uow:
            revoked_ids = await self.uow.sessions.revoke_all_except(
                user_id,
                current_fingerprint,
            )
            for session_id in revoked_ids:
                await self.notifier.notify_session_revoked(
                    str(user_id),
                    str(session_id),
                )
            await self.uow.commit()

        if revoked_ids:
            await self.clear_sessions_cache_bulk(revoked_ids)

    async def revoke_all_user_sessions(self, user_id: UUID) -> None:
        """Отзывает все сессии пользователя."""
        async with self.uow:
            revoked_ids = await self.uow.sessions.revoke_all_for_user(user_id)
            for session_id in revoked_ids:
                await self.notifier.notify_session_revoked(
                    str(user_id),
                    str(session_id),
                )
            await self.uow.commit()

        if revoked_ids:
            await self.clear_sessions_cache_bulk(revoked_ids)

    async def get_user_and_session_id(self, token: str) -> tuple[dtos.UserDTO, str]:
        """Получает пользователя и session_id по access token."""
        payload = await self.token_service.get_token_payload(token)

        user_id = self._get_required_payload_value(payload, "sub")
        session_id = self._get_required_payload_value(payload, "sid")

        session_cache_key = redis_keys.get_session_key(session_id)
        session_cache = await self._get_valid_session_cache(session_cache_key)

        if session_cache is None:
            user_dto = await self._get_user_by_session_from_db(
                user_id=user_id,
                session_id=session_id,
            )

            if not user_dto.is_active:
                raise exceptions.UserInactiveError()

            return user_dto, session_id

        user_dto = await self._get_user_from_cache_or_db(user_id)

        if not user_dto.is_active:
            raise exceptions.UserInactiveError()

        return user_dto, session_id

    async def update_activity(self, session_id: UUID) -> None:
        """Обновляет последнюю активность сессии с Redis-троттлингом."""
        throttle_key = f"auth:session:activity:{session_id}"

        should_update = await self.redis.set(
            throttle_key,
            "1",
            ex=ACTIVITY_THROTTLE_SECONDS,
            nx=True,
        )

        if not should_update:
            return

        async with self.uow:
            await self.uow.sessions.update_last_activity(
                session_id,
                time.utc_now(),
            )
            await self.uow.commit()

    async def update_user_retention_settings(self, user_id: UUID, days: int) -> None:
        """Обновляет пользовательский срок хранения сессий."""
        async with self.uow:
            await self.uow.users.update_retention_days(user_id, days)
            await self.uow.commit()

        await self.invalidate_user_cache(user_id)

    async def verify_session_fast(self, session_id: str) -> bool:
        """Быстро проверяет сессию только через Redis cache.

        Используется API Gateway. Метод намеренно не ходит в базу данных.
        """
        session_key = redis_keys.get_session_key(session_id)
        session_cache = await self._get_valid_session_cache(session_key)

        return session_cache is not None

    async def _refresh_session_locked(self, fingerprint: str) -> tuple[str, str]:
        """Обновляет сессию внутри refresh lock."""
        async with self.uow:
            session = await self.uow.sessions.get_by_fingerprint(fingerprint)
            if not session:
                raise exceptions.InvalidTokenError("Invalid refresh token")

            if session.expires_at < time.utc_now():
                session.revoked = True
                session_id = session.session_id
                await self.uow.commit()

                await self.clear_session_cache(session_id)

                raise exceptions.InvalidTokenError("Refresh token expired")

            user = await self.uow.users.get_by_id(session.user_id)
            if not user:
                raise exceptions.UserNotFoundError("User not found")

            new_refresh_token = str(uuid4())
            new_fingerprint = crypto.hash_token(new_refresh_token)
            new_expires_at = time.utc_now() + timedelta(
                days=user.retention_days or DEFAULT_RETENTION_DAYS,
            )

            await self.uow.sessions.update_fingerprint(
                session=session,
                new_fingerprint=new_fingerprint,
                new_expires_at=new_expires_at,
            )

            new_access_token = self.token_service.create_access_token(
                user_id=str(user.user_id),
                role=user.role,
                session_id=str(session.session_id),
            )

            await self.notifier.notify_token_refreshed(str(user.user_id))

            session_dto = session_to_dto(session)
            session_dto.is_current = True
            user_dto = user_to_dto(user)

            await self.uow.commit()

        await self.activate_session_in_cache(session_dto, user_dto)

        return new_access_token, new_refresh_token

    async def _get_user_by_session_from_db(
        self,
        user_id: str,
        session_id: str,
    ) -> dtos.UserDTO:
        """Проверяет сессию в БД и возвращает пользователя."""
        async with self.uow:
            session = await self.uow.sessions.get_active_by_id(UUID(session_id))
            if not session:
                raise exceptions.InvalidTokenError("Session revoked or expired")

            user = await self.uow.users.get_by_id(UUID(user_id))
            if not user:
                raise exceptions.UserNotFoundError("User not found")

            session_dto = session_to_dto(session)
            user_dto = user_to_dto(user)

        await self.activate_session_in_cache(session_dto, user_dto)

        return user_dto

    async def _get_user_from_cache_or_db(self, user_id: str) -> dtos.UserDTO:
        """Получает пользователя из Redis cache или БД."""
        cache_key = redis_keys.get_user_cache_key(user_id)
        cached_user = await self.redis.get(cache_key)

        if cached_user:
            try:
                return dtos.UserDTO.model_validate_json(cached_user)
            except Exception:
                logger.warning(
                    "Failed to parse cached user %s",
                    user_id,
                    exc_info=True,
                )
                await self.redis.delete(cache_key)

        async with self.uow:
            user = await self.uow.users.get_by_id(UUID(user_id))
            if not user:
                raise exceptions.UserNotFoundError("User not found")

            user_dto = user_to_dto(user)

        await self.cache_user_data(user_dto)

        return user_dto

    async def _get_valid_session_cache(self, session_key: str) -> dict | None:
        """Возвращает валидный cache сессии или None."""
        cached_raw = await self.redis.get(session_key)
        if not cached_raw:
            return None

        try:
            session_data = orjson.loads(cached_raw)
        except Exception:
            logger.warning(
                "Failed to parse cached session %s",
                session_key,
                exc_info=True,
            )
            await self.redis.delete(session_key)
            return None

        exp_timestamp = session_data.get("exp")
        if not exp_timestamp:
            await self.redis.delete(session_key)
            return None

        if time.utc_timestamp() > exp_timestamp:
            await self.redis.delete(session_key)
            return None

        return session_data

    @staticmethod
    def _build_session_cache_payload(
        session_dto: dtos.SessionDTO,
        user_dto: dtos.UserDTO,
    ) -> bytes:
        """Формирует payload кэша сессии."""
        return orjson.dumps(
            {
                "uid": str(user_dto.user_id),
                "role": user_dto.role.value,
                "exp": session_dto.expires_at.timestamp(),
            },
        )

    @staticmethod
    def _get_required_payload_value(payload: dict, key: str) -> str:
        """Достает обязательное строковое значение из JWT payload."""
        value = payload.get(key)

        if not value:
            raise exceptions.InvalidTokenStructureError(
                f"Missing required token field: {key}",
            )

        return str(value)

    @property
    def _session_cache_ttl_seconds(self) -> int:
        """TTL кэша сессии в секундах."""
        return int(
            timedelta(
                days=settings.JWT.SESSION_CACHE_EXPIRE_DAYS,
            ).total_seconds(),
        )
