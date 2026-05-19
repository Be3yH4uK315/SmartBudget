from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from arq.connections import ArqRedis

from app.core import config
from app.domain.schemas import dtos
from app.infrastructure.db import uow
from app.utils import email_templates
from smartbudget_shared.events import (
    AuthEventType,
    AuthUserPayload,
    create_auth_event,
)

settings = config.settings


def _utc_now() -> datetime:
    """Возвращает текущее UTC-время."""
    return datetime.now(timezone.utc)


class AuthNotifier:
    """Сервис постановки уведомлений и auth-событий в очередь."""

    def __init__(
        self,
        uow: uow.UnitOfWork,
        arq_pool: ArqRedis,
    ) -> None:
        self.uow = uow
        self.arq = arq_pool

    async def _save_event(
        self,
        event_type: AuthEventType,
        **payload_fields: Any,
    ) -> None:
        """Сохраняет auth-событие в outbox для последующей публикации в Kafka."""

        def _none_if_empty(value: Any) -> Any:
            """Возвращает None вместо пустой строки."""
            if isinstance(value, str) and not value.strip():
                return None

            return value

        payload = AuthUserPayload(
            user_id=_none_if_empty(payload_fields.get("user_id")),
            email=_none_if_empty(payload_fields.get("email")),
            old_email=_none_if_empty(payload_fields.get("old_email")),
            new_email=_none_if_empty(payload_fields.get("new_email")),
            name=_none_if_empty(payload_fields.get("name")),
            language=_none_if_empty(payload_fields.get("language")),
            session_id=_none_if_empty(payload_fields.get("session_id")),
            ip=_none_if_empty(payload_fields.get("ip")),
            device=_none_if_empty(payload_fields.get("device")),
            location=_none_if_empty(payload_fields.get("location")),
            reason=_none_if_empty(payload_fields.get("reason")),
            logged_at=payload_fields.get("logged_at"),
            changed_at=payload_fields.get("changed_at"),
            detected_at=payload_fields.get("detected_at"),
        )

        event = create_auth_event(
            event_type=event_type,
            payload=payload,
        )

        self.uow.outbox.add_event(
            topic=settings.KAFKA.producer_topic,
            payload=event.model_dump(
                mode="json",
                by_alias=True,
                exclude_none=True,
            ),
            event_type=event_type.value,
        )

    async def enrich_session(
        self,
        session_id: UUID,
        ip: str,
        user_agent: str,
    ) -> None:
        """Ставит задачу обогащения сессии в ARQ."""
        await self.arq.enqueue_job(
            "enrich_session_task",
            session_id=session_id,
            ip=ip,
            user_agent=user_agent,
        )

    async def send_verification_email(self, email: str, token: str) -> None:
        """Ставит задачу отправки письма верификации email."""
        await self.arq.enqueue_job(
            "send_email_task",
            to=email,
            subject="Подтвердите email",
            body=email_templates.get_verification_email_body(email, token),
        )

    async def send_password_reset_email(self, email: str, token: str) -> None:
        """Ставит задачу отправки письма для сброса пароля."""
        await self.arq.enqueue_job(
            "send_email_task",
            to=email,
            subject="Сброс пароля",
            body=email_templates.get_password_reset_body(email, token),
        )

    async def send_change_email_confirmation(
        self,
        new_email: str,
        token: str,
        user_id: str,
    ) -> None:
        """Ставит задачу отправки письма для подтверждения смены email."""
        await self.arq.enqueue_job(
            "send_email_task",
            to=new_email,
            subject="Подтвердите смену email",
            body=email_templates.get_change_email_body(new_email, token),
        )

    async def notify_registration(
        self,
        user: dtos.UserDTO,
        ip: str,
        location: str,
    ) -> None:
        """Сохраняет событие регистрации пользователя."""
        await self._save_event(
            AuthEventType.USER_REGISTERED,
            user_id=str(user.user_id),
            email=user.email,
            language=user.language.value,
            name=user.name,
            ip=ip,
            location=location,
        )

    async def notify_login(
        self,
        user: dtos.UserDTO,
        ip: str,
        location: str,
        device: str | None = None,
    ) -> None:
        """Сохраняет событие нового входа пользователя для security-уведомления."""
        await self._save_event(
            AuthEventType.DEVICE_NEW_LOGIN,
            user_id=str(user.user_id),
            email=user.email,
            language=user.language.value,
            name=user.name,
            ip=ip,
            device=device,
            location=location,
            logged_at=_utc_now(),
        )

    async def notify_login_failed(
        self,
        email: str,
        ip: str,
        location: str,
    ) -> None:
        """Обрабатывает неуспешный вход.

        Событие не публикуется, потому что для внешнего auth-события нужен user_id.
        """
        return None

    async def notify_suspicious_activity(
        self,
        user: dtos.UserDTO,
        reason: str,
        ip: str | None = None,
        location: str | None = None,
        device: str | None = None,
    ) -> None:
        """Сохраняет событие подозрительной активности."""
        await self._save_event(
            AuthEventType.ACTIVITY_SUSPICIOUS,
            user_id=str(user.user_id),
            email=user.email,
            language=user.language.value,
            name=user.name,
            reason=reason,
            ip=ip,
            device=device,
            location=location,
            detected_at=_utc_now(),
        )

    async def notify_email_verified(self, email: str) -> None:
        """Обрабатывает успешную валидацию email-токена."""
        return None

    async def notify_password_reset_validated(self, email: str) -> None:
        """Обрабатывает успешную валидацию reset-токена."""
        return None

    async def notify_password_reset_completed(self, user: dtos.UserDTO) -> None:
        """Сохраняет событие смены пароля после сброса."""
        await self._save_event(
            AuthEventType.PASSWORD_CHANGED,
            user_id=str(user.user_id),
            email=user.email,
            language=user.language.value,
            name=user.name,
            changed_at=_utc_now(),
        )

    async def notify_password_changed(
        self,
        user_id: str,
        email: str | None = None,
        language: str | None = None,
        name: str | None = None,
    ) -> None:
        """Сохраняет событие смены пароля."""
        payload: dict[str, Any] = {
            "user_id": user_id,
            "changed_at": _utc_now(),
        }

        if email:
            payload["email"] = email

        if language:
            payload["language"] = language

        if name:
            payload["name"] = name

        await self._save_event(
            AuthEventType.PASSWORD_CHANGED,
            **payload,
        )

    async def notify_logout(self, user_id: str) -> None:
        """Сохраняет событие выхода пользователя."""
        await self._save_event(
            AuthEventType.USER_LOGOUT,
            user_id=user_id,
        )

    async def notify_token_refreshed(self, user_id: str) -> None:
        """Обрабатывает обновление токенов без публикации внешнего события."""
        return None

    async def notify_session_revoked(
        self,
        user_id: str,
        session_id: str,
    ) -> None:
        """Сохраняет событие отзыва пользовательской сессии."""
        await self._save_event(
            AuthEventType.SESSION_REVOKED,
            user_id=user_id,
            session_id=session_id,
        )

    async def notify_profile_updated(
        self,
        user_id: str,
        email: str | None = None,
        language: str | None = None,
        name: str | None = None,
    ) -> None:
        """Сохраняет событие обновления профиля."""
        payload: dict[str, str] = {"user_id": user_id}

        if email:
            payload["email"] = email

        if language:
            payload["language"] = language

        if name:
            payload["name"] = name

        await self._save_event(
            AuthEventType.PROFILE_UPDATED,
            **payload,
        )

    async def notify_email_changed(
        self,
        user_id: str,
        old_email: str,
        new_email: str,
    ) -> None:
        """Сохраняет событие смены email."""
        await self._save_event(
            AuthEventType.EMAIL_CHANGED,
            user_id=user_id,
            old_email=old_email,
            new_email=new_email,
        )
