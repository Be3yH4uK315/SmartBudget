import logging
from datetime import datetime, timedelta, timezone

from jwt import encode, decode, PyJWTError
from app.core import config, exceptions
from app.domain.schemas import api as api_schemas

logger = logging.getLogger(__name__)
settings = config.settings

class TokenService:
    """Сервис для работы с JWT токенами."""

    def create_access_token(self, user_id: str, role: int, session_id: str) -> str:
        """Генерирует JWT access token."""
        payload = {
            "sub": user_id,
            "sid": session_id,
            "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.JWT.ACCESS_TOKEN_EXPIRE_MINUTES),
            "role": api_schemas.UserRole(role).value,
            "iss": settings.JWT.JWT_ISSUER,
            "aud": settings.JWT.JWT_AUDIENCE,
        }
        return encode(
            payload,
            settings.JWT.JWT_PRIVATE_KEY,
            algorithm=settings.JWT.JWT_ALGORITHM,
        )
    
    def decode_token(self, token: str, verify_exp: bool = True) -> dict:
        """Декодирует токен и возвращает payload."""
        try:
            return decode(
                token,
                settings.JWT.JWT_PUBLIC_KEY,
                algorithms=[settings.JWT.JWT_ALGORITHM],
                audience=settings.JWT.JWT_AUDIENCE,
                options={"verify_exp": verify_exp, "require": ["exp", "sub", "sid"]}
            )
        except PyJWTError as e:
            logger.debug(f"Token decoding failed: {e}")
            raise exceptions.InvalidTokenError("Invalid token")

    def get_token_payload(self, token: str) -> dict:
        """Обертка для безопасного получения данных."""
        return self.decode_token(token, verify_exp=True)

    def get_user_id_from_expired_token(self, token: str) -> str | None:
        """Извлекает sub из токена, игнорируя срок действия (для логаута)."""
        try:
            payload = self.decode_token(token, verify_exp=False)
            return payload.get("sub")
        except exceptions.InvalidTokenError:
            return None