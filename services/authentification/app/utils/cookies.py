from fastapi import Response
from app.core.config import settings

def set_auth_cookies(
    response: Response,
    access_token: str,
    refresh_token: str
):
    """Хелпер для установки httpOnly cookie."""
    secure = (settings.APP.ENV == 'prod')
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=secure,
        samesite='None',
        path='/',
        max_age=900,  # 15 min
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=secure,
        samesite='None',
        path='/',
        max_age=2592000,  # 30 days
    )

def delete_auth_cookies(response: Response):
    """Хелпер для удаления auth cookie."""
    secure = (settings.APP.ENV == 'prod')
    response.delete_cookie("access_token", httponly=True, secure=secure, samesite='None', path='/')
    response.delete_cookie("refresh_token", httponly=True, secure=secure, samesite='None', path='/')
