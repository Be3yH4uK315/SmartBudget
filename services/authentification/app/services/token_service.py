import asyncio
import logging
from datetime import timedelta
from typing import Any

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from jwt import PyJWTError, decode, encode

from app.core import config, exceptions
from app.domain.schemas import api as api_schemas
from app.utils import crypto, time

logger = logging.getLogger(__name__)
settings = config.settings


class TokenService:
    """Сервис для работы с JWT токенами."""

    def create_access_token(self, user_id: str, role: int, session_id: str) -> str:
        """Создает JWT access token."""
        payload = {
            "sub": user_id,
            "sid": session_id,
            "exp": time.utc_now()
            + timedelta(minutes=settings.JWT.ACCESS_TOKEN_EXPIRE_MINUTES),
            "role": api_schemas.UserRole(role).value,
            "iss": settings.JWT.JWT_ISSUER,
            "aud": settings.JWT.JWT_AUDIENCE,
        }

        return encode(
            payload,
            settings.JWT.JWT_PRIVATE_KEY,
            algorithm=settings.JWT.JWT_ALGORITHM,
        )

    def _decode_sync(self, token: str, verify_exp: bool) -> dict[str, Any]:
        """Синхронно декодирует JWT token."""
        options = {
            "verify_exp": verify_exp,
            "require": ["exp", "sub", "sid"],
        }

        return decode(
            token,
            settings.JWT.JWT_PUBLIC_KEY,
            algorithms=[settings.JWT.JWT_ALGORITHM],
            audience=settings.JWT.JWT_AUDIENCE,
            issuer=settings.JWT.JWT_ISSUER,
            options=options,
        )

    async def decode_token(
        self,
        token: str,
        verify_exp: bool = True,
    ) -> dict[str, Any]:
        """Асинхронно декодирует JWT token."""
        loop = asyncio.get_running_loop()

        try:
            return await loop.run_in_executor(
                None,
                self._decode_sync,
                token,
                verify_exp,
            )
        except PyJWTError as exc:
            logger.debug("Token decoding failed: %s", exc)
            raise exceptions.InvalidTokenError("Invalid token") from exc

    async def get_token_payload(self, token: str) -> dict[str, Any]:
        """Возвращает payload валидного access token."""
        return await self.decode_token(token, verify_exp=True)

    async def get_user_id_from_expired_token(self, token: str) -> str | None:
        """Извлекает user_id из token, игнорируя срок действия."""
        try:
            payload = await self.decode_token(token, verify_exp=False)
        except exceptions.InvalidTokenError:
            return None

        user_id = payload.get("sub")
        return str(user_id) if user_id else None

    def get_jwks(self) -> dict[str, list[dict[str, str]]]:
        """Возвращает публичный ключ JWT в формате JWKS."""
        public_key_obj = serialization.load_pem_public_key(
            settings.JWT.JWT_PUBLIC_KEY.encode(),
            backend=default_backend(),
        )

        numbers = public_key_obj.public_numbers()

        return {
            "keys": [
                {
                    "kty": "RSA",
                    "use": "sig",
                    "kid": "sig-1",
                    "alg": settings.JWT.JWT_ALGORITHM,
                    "n": crypto.int_to_base64url(numbers.n),
                    "e": crypto.int_to_base64url(numbers.e),
                },
            ],
        }
