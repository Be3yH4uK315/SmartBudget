from app.infrastructure.db import models
from app.domain.schemas.dtos import SessionDTO


def session_to_dto(session: models.Session) -> SessionDTO:
    """Безопасный mapper ORM → DTO."""
    return SessionDTO(
        session_id=session.session_id,
        user_id=session.user_id,
        user_agent=session.user_agent,
        device_name=session.device_name,
        ip=session.ip,
        location=session.location,
        revoked=session.revoked,
        refresh_fingerprint=session.refresh_fingerprint,
        last_activity=session.last_activity,
        expires_at=session.expires_at,
        created_at=session.created_at,
    )