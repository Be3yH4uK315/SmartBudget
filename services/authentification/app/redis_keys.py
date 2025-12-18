def getVerifyEmailKey(email: str) -> str:
    """Ключ Redis для токена верификации email."""
    return f"verify:{email}"

def getResetPasswordKey(email: str) -> str:
    """Ключ Redis для токена сброса пароля."""
    return f"reset:{email}"

def getLoginFailKey(ip: str) -> str:
    """Ключ Redis для отслеживания неудачных попыток входа по IP."""
    return f"fail:{ip}"