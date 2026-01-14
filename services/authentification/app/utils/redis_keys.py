def get_verify_email_key(email: str) -> str:
    """Ключ Redis для токена верификации email."""
    return f"auth:verify:{email}"

def get_reset_password_key(email: str) -> str:
    """Ключ Redis для токена сброса пароля."""
    return f"auth:reset:{email}"

def get_login_fail_key(ip: str) -> str:
    """Ключ Redis для отслеживания неудачных попыток входа по IP."""
    return f"auth:fail:{ip}"

def get_session_key(session_id: str) -> str:
    """Ключ для кэширования активной сессии."""
    return f"auth:session:active:{session_id}"

def get_user_cache_key(user_id: str) -> str:
    """Ключ для кэширования объекта User."""
    return f"auth:user:data:{user_id}"