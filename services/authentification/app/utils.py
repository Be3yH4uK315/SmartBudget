from user_agents import parse as ua_parse
import ipaddress
import geoip2.database
from geoip2.errors import AddressNotFoundError
from hashlib import sha256
from bcrypt import hashpw, gensalt, checkpw
from logging import getLogger
from functools import lru_cache

logger = getLogger(__name__)

def parse_device(user_agent: str) -> str:
    """Анализирует информацию об устройстве из User-Agent."""
    ua = ua_parse(user_agent)
    return f"{ua.device.family}, {ua.os.family} {ua.os.version_string}"

@lru_cache(maxsize=1024)
def get_location(ip: str, reader: geoip2.database.Reader) -> dict:
    """Получает местоположение по IP-адресу с помощью GeoIP."""
    try:
        if ipaddress.ip_address(ip).is_private:
            return {"type": "local", "country": None, "city": None, "full": "Local Network"}
    except ValueError:
        pass

    try:
        geo = reader.city(ip)
        return {
            "type": "geo",
            "country": geo.country.name,
            "city": geo.city.name or "Unknown",
            "full": f"{geo.country.name}, {geo.city.name or 'Unknown'}"
        }
    except (AddressNotFoundError, Exception) as e:
        logger.warning(f"GeoIP failed for IP {ip}: {e}")
        return {"type": "unknown", "country": None, "city": None, "full": "Unknown"}

def hash_token(token: str) -> str:
    """Хэширует токен."""
    return sha256(token.encode()).hexdigest()

def hash_password(password: str) -> str:
    """Хэширует пароль."""
    return hashpw(password.encode(), gensalt()).decode()

def check_password(password: str, hashed: str) -> bool:
    """Проверяет пароль."""
    return checkpw(password.encode(), hashed.encode())