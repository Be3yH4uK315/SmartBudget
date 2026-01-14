import logging
from uuid import UUID

from arq.connections import ArqRedis

from app.core import config
from app.infrastructure.db import uow
from app.domain.schemas import kafka as k_schemas
from app.domain.schemas import dtos
from app.utils import email_templates


logger = logging.getLogger(__name__)
settings = config.settings


class AuthNotifier:
    """Сервис уведомлений."""

    def __init__(self, uow: uow.UnitOfWork, arq_pool: ArqRedis):
        self.uow = uow
        self.arq = arq_pool

    async def _save_event(
        self,
        event_type: k_schemas.AuthEventTypes,
        **kwargs,
    ) -> None:
        payload = {
            "event_type": event_type.value,
            **kwargs,
        }

        await self.uow.users.add_outbox_event(
            topic=settings.KAFKA.KAFKA_AUTH_EVENTS_TOPIC,
            event_data=payload,
        )

    async def enrich_session(
        self,
        session_id: UUID,
        ip: str,
        user_agent: str,
    ) -> None:
        await self.arq.enqueue_job(
            "enrich_session_task",
            session_id=session_id,
            ip=ip,
            user_agent=user_agent,
        )

    async def send_verification_email(self, email: str, token: str) -> None:
        email_body = email_templates.get_verification_email_body(email, token)

        await self.arq.enqueue_job(
            "send_email_task",
            to=email,
            subject="Verify your email",
            body=email_body,
        )

        await self._save_event(
            k_schemas.AuthEventTypes.VERIFICATION_STARTED,
            email=email,
        )

    async def send_password_reset_email(self, email: str, token: str) -> None:
        await self.arq.enqueue_job(
            "send_email_task",
            to=email,
            subject="Reset your password",
            body=email_templates.get_password_reset_body(email, token),
        )

        await self._save_event(
            k_schemas.AuthEventTypes.PASSWORD_RESET_STARTED,
            email=email,
        )

    async def notify_registration(
        self,
        user: dtos.UserDTO,
        ip: str,
        location: str,
    ) -> None:
        await self._save_event(
            k_schemas.AuthEventTypes.USER_REGISTERED,
            user_id=str(user.user_id),
            email=user.email,
            name=user.name,
            ip=ip,
            location=location,
        )

    async def notify_login(
        self,
        user: dtos.UserDTO,
        ip: str,
        location: str,
    ) -> None:
        await self._save_event(
            k_schemas.AuthEventTypes.USER_LOGIN,
            user_id=str(user.user_id),
            email=user.email,
            ip=ip,
            location=location,
        )

    async def notify_login_failed(
        self,
        email: str,
        ip: str,
        location: str,
    ) -> None:
        await self._save_event(
            k_schemas.AuthEventTypes.USER_LOGIN_FAILED,
            email=email,
            ip=ip,
            location=location,
        )

    async def notify_email_verified(self, email: str) -> None:
        await self._save_event(
            k_schemas.AuthEventTypes.VERIFICATION_VALIDATED,
            email=email,
        )

    async def notify_password_reset_validated(self, email: str) -> None:
        await self._save_event(
            k_schemas.AuthEventTypes.PASSWORD_RESET_VALIDATED,
            email=email,
        )

    async def notify_password_reset_completed(
        self,
        user: dtos.UserDTO,
    ) -> None:
        await self._save_event(
            k_schemas.AuthEventTypes.PASSWORD_RESET_COMPLETED,
            user_id=str(user.user_id),
            email=user.email,
        )

    async def notify_password_changed(self, user_id: str) -> None:
        await self._save_event(
            k_schemas.AuthEventTypes.PASSWORD_CHANGED,
            user_id=user_id,
        )

    async def notify_logout(self, user_id: str) -> None:
        await self._save_event(
            k_schemas.AuthEventTypes.USER_LOGOUT,
            user_id=user_id,
        )

    async def notify_token_refreshed(self, user_id: str) -> None:
        """Событие: обновление access/refresh токенов."""
        await self._save_event(
            k_schemas.AuthEventTypes.TOKEN_REFRESHED,
            user_id=user_id,
        )

    async def notify_session_revoked(
        self,
        user_id: str,
        session_id: str,
    ) -> None:
        """Событие: отзыв пользовательской сессии."""
        await self._save_event(
            k_schemas.AuthEventTypes.SESSION_REVOKED,
            user_id=user_id,
            session_id=session_id,
        )