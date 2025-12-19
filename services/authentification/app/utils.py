from user_agents import parse as ua_parse
import ipaddress
import geoip2.database
from geoip2.errors import AddressNotFoundError
from hashlib import sha256
from bcrypt import hashpw, gensalt, checkpw
from logging import getLogger

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