from functools import lru_cache

from fastapi import APIRouter

from app.services.token_service import TokenService

router = APIRouter(tags=["jwks"])


@router.get("/.well-known/jwks.json")
async def get_jwks():
    """Возвращает публичные ключи JWT в формате JWKS."""
    return _get_cached_jwks()


@lru_cache(maxsize=1)
def _get_cached_jwks():
    return TokenService().get_jwks()
