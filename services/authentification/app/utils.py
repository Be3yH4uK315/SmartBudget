import base64
from user_agents import parse as ua_parse
import ipaddress
import geoip2.database
from geoip2.errors import AddressNotFoundError
from hashlib import sha256
from bcrypt import hashpw, gensalt, checkpw
from logging import getLogger
import json
from decimal import Decimal
from datetime import date, datetime
from uuid import UUID
from enum import Enum
from typing import Any

from app import exceptions

logger = getLogger(__name__)

def parse_device(user_agent: str) -> str:
    """Анализирует информацию об устройстве из User-Agent."""
    try:
        ua = ua_parse(user_agent)
        device_family = ua.device.family or "Unknown"
        os_family = ua.os.family or "Unknown"
        os_version = ua.os.version_string or ""
        
        device_str = f"{device_family}, {os_family}"
        if os_version:
            device_str += f" {os_version}"
        
        return device_str[:255]
    except Exception as e:
        logger.warning(f"Failed to parse user agent: {e}")
        return "Unknown Device"

def get_location(ip: str, reader: geoip2.database.Reader | None) -> dict:
    """Получает местоположение по IP-адресу."""
    if not reader:
        return {"type": "unknown", "country": None, "city": None, "full": "Unknown"}
    
    try:
        try:
            ip_obj = ipaddress.ip_address(ip)
            if ip_obj.is_private:
                return {
                    "type": "local",
                    "country": None,
                    "city": None,
                    "full": "Local Network"
                }
        except ValueError as e:
            logger.warning(f"Invalid IP format: {ip}, error: {e}")
            return {"type": "unknown", "country": None, "city": None, "full": "Unknown"}

        geo = reader.city(ip)
        return {
            "type": "geo",
            "country": geo.country.name or "Unknown",
            "city": geo.city.name or "Unknown",
            "full": f"{geo.country.name or 'Unknown'}, {geo.city.name or 'Unknown'}"
        }
    except AddressNotFoundError:
        logger.debug(f"GeoIP: Address not found in database: {ip}")
        return {"type": "unknown", "country": None, "city": None, "full": "Unknown"}
    except Exception as e:
        logger.error(f"GeoIP error for IP {ip}: {e}")
        return {"type": "unknown", "country": None, "city": None, "full": "Unknown"}

def hash_token(token: str) -> str:
    """Хэширует токен."""
    return sha256(token.encode()).hexdigest()

def hash_password(password: str) -> str:
    """Хэширует пароль с использованием bcrypt."""
    try:
        salt = gensalt(rounds=12)
        return hashpw(password.encode(), salt).decode()
    except Exception as e:
        logger.error(f"Password hashing failed: {e}")
        raise exceptions.DatabaseError("Password hashing failed")

def check_password(password: str, hashed: str) -> bool:
    """Проверяет пароль против хэша."""
    try:
        return checkpw(password.encode(), hashed.encode())
    except Exception as e:
        logger.error(f"Password check failed: {e}")
        return False

def validate_password_strength(password: str) -> tuple[bool, str]:
    """Проверяет надежность пароля."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit"
    
    if not any(c in "!@#$%^&*()-_=+[]{}|;:,.<>?" for c in password):
        return False, "Password must contain at least one special character"
    
    return True, ""

def int_to_base64url(value: int) -> str:
    """Преобразует целое число в строку base64url. Используется для JWKS."""
    byte_len = (value.bit_length() + 7) // 8
    if byte_len == 0:
        byte_len = 1
    bytes_val = value.to_bytes(byte_len, "big", signed=False)
    return base64.urlsafe_b64encode(bytes_val).decode("utf-8").rstrip("=")

def app_json_serializer(obj: Any) -> Any:
    """Универсальный сериализатор для всего проекта."""
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, Enum):
        return obj.value
    raise TypeError(f"Type {type(obj)} not serializable")

def to_json_str(data: Any) -> str:
    """Сериализует объект в JSON строку."""
    return json.dumps(data, default=app_json_serializer, ensure_ascii=False)

def recursive_normalize(obj: Any) -> Any:
    """Рекурсивно приводит типы к примитивам (для сохранения в Redis/DB)."""
    if isinstance(obj, dict):
        return {k: recursive_normalize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [recursive_normalize(v) for v in obj]
    if isinstance(obj, (Decimal, date, datetime, UUID, Enum)):
        return app_json_serializer(obj)
    return obj