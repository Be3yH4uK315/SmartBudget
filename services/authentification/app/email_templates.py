from urllib.parse import quote

from app import settings

def getVerificationEmailBody(email: str, token: str) -> str:
    """Генерирует тело письма для верификации аккаунта."""
    encodedEmail = quote(email)
    verifyUrl = f"{settings.settings.APP.FRONTEND_URL}/auth/registration?token={token}&email={encodedEmail}"

    return f"""
    Здравствуйте!

    Чтобы завершить регистрацию в Budget App, пожалуйста, перейдите по ссылке ниже:
    {verifyUrl}

    Ссылка действительна в течение 15 минут.

    Если вы не регистрировались, просто проигнорируйте это письмо.
    """

def getPasswordResetBody(email: str, token: str) -> str:
    """Генерирует тело письма для сброса пароля."""
    encodedEmail = quote(email)
    resetUrl = f"{settings.settings.APP.FRONTEND_URL}/auth/reset-password?token={token}&email={encodedEmail}"
    
    return f"""
    Здравствуйте!

    Вы (или кто-то другой) запросили сброс пароля для вашего аккаунта Budget App.
    Перейдите по ссылке ниже, чтобы установить новый пароль:
    {resetUrl}

    Ссылка действительна в течение 15 минут.

    Если вы не запрашивали сброс, просто проигнорируйте это письмо.
    """