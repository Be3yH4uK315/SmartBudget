import asyncio
import base64
from hashlib import sha256
from bcrypt import hashpw, gensalt, checkpw

def hash_token(token: str) -> str:
    """Быстрое хеширование (SHA256) для технических токенов (email, refresh)."""
    return sha256(token.encode()).hexdigest()

def _hash_password_sync(password: str) -> str:
    """Внутренняя синхронная функция."""
    salt = gensalt(rounds=10) 
    return hashpw(password.encode(), salt).decode()

def _check_password_sync(password: str, hashed: str) -> bool:
    """Внутренняя синхронная проверка."""
    try:
        return checkpw(password.encode(), hashed.encode())
    except Exception:
        return False

async def hash_password(password: str) -> str:
    """Асинхронное хеширование."""
    return await asyncio.to_thread(_hash_password_sync, password)

async def check_password(password: str, hashed: str) -> bool:
    """Асинхронная проверка пароля."""
    return await asyncio.to_thread(_check_password_sync, password, hashed)

def int_to_base64url(value: int) -> str:
    """Вспомогательная функция для JWKS."""
    byte_len = (value.bit_length() + 7) // 8
    if byte_len == 0:
        byte_len = 1
    bytes_val = value.to_bytes(byte_len, "big", signed=False)
    return base64.urlsafe_b64encode(bytes_val).decode("utf-8").rstrip("=")
