from app.domain.schemas.dtos import SessionDTO
from app.infrastructure.db import models


def session_to_dto(session: models.Session) -> SessionDTO:
    """Преобразует ORM-модель сессии во внутренний DTO."""
    return SessionDTO(
        session_id=session.session_id,
        user_id=session.user_id,
        user_agent=session.user_agent,
        device_name=session.device_name,
        ip=session.ip,
        location=session.location or "Unknown",
        revoked=session.revoked,
        refresh_fingerprint=session.refresh_fingerprint,
        last_activity=session.last_activity,
        expires_at=session.expires_at,
        created_at=session.created_at,
    )
