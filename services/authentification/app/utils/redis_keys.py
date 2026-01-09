def get_verify_email_key(email: str) -> str:
    """Ключ Redis для токена верификации email."""
    return f"verify:{email}"

def get_reset_password_key(email: str) -> str:
    """Ключ Redis для токена сброса пароля."""
    return f"reset:{email}"

def get_login_fail_key(ip: str) -> str:
    """Ключ Redis для отслеживания неудачных попыток входа по IP."""
    return f"fail:{ip}"

def get_session_key(session_id: str) -> str:
    """Ключ для кэширования активной сессии."""
    return f"session:active:{session_id}"