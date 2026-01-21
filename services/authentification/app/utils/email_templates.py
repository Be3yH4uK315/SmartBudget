from urllib.parse import quote
from app.core.config import settings

def get_verification_email_body(email: str, token: str) -> str:
    """Генерирует тело письма для верификации аккаунта."""
    encoded_email = quote(email)
    verify_url = f"{settings.APP.FRONTEND_URL}/auth/registration?token={token}&email={encoded_email}"

    return f"""
    Здравствуйте!

    Чтобы завершить регистрацию в Budget App, пожалуйста, перейдите по ссылке ниже:
    {verify_url}

    Ссылка действительна в течение 15 минут.

    Если вы не регистрировались, просто проигнорируйте это письмо.
    """

def get_password_reset_body(email: str, token: str) -> str:
    """Генерирует тело письма для сброса пароля."""
    encoded_email = quote(email)
    reset_url = f"{settings.APP.FRONTEND_URL}/auth/reset-password?token={token}&email={encoded_email}"
    
    return f"""
    Здравствуйте!

    Вы (или кто-то другой) запросили сброс пароля для вашего аккаунта Budget App.
    Перейдите по ссылке ниже, чтобы установить новый пароль:
    {reset_url}

    Ссылка действительна в течение 15 минут.

    Если вы не запрашивали сброс, просто проигнорируйте это письмо.
    """

def get_change_email_body(new_email: str, token: str) -> str:
    """Генерирует тело письма для подтверждения смены email."""
    confirm_url = f"{settings.APP.FRONTEND_URL}/profile/change-email/confirm?token={token}"
    
    return f"""
    Здравствуйте!

    Поступил запрос на смену Email адреса вашего аккаунта на {new_email}.
    
    Для подтверждения перехода на новый адрес, нажмите на ссылку:
    {confirm_url}

    Ссылка действительна в течение 15 минут.
    
    Если вы не инициировали это действие, срочно смените пароль, так как ваш аккаунт может быть скомпрометирован.
    """