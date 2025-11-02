from user_agents import parse as ua_parse
import ipaddress
import geoip2.database
from geoip2.errors import AddressNotFoundError
from hashlib import sha256
from bcrypt import hashpw, gensalt, checkpw
from logging import getLogger

logger = getLogger(__name__)

def parse_device(user_agent: str) -> str:
    ua = ua_parse(user_agent)
    return f"{ua.device.family}, {ua.os.family} {ua.os.version_string}"

def get_location(ip: str, reader: geoip2.database.Reader) -> str:
    try:
        if ipaddress.ip_address(ip).is_private:
            return "Local Network"
    except ValueError:
        pass

    try:
        geo = reader.city(ip)
        return f"{geo.country.name}, {geo.city.name or 'Unknown'}"
    except (AddressNotFoundError, Exception) as e:
        logger.warning(f"GeoIP failed for IP {ip}: {e}")
        return "Unknown"

def hash_token(token: str) -> str:
    return sha256(token.encode()).hexdigest()

def hash_password(password: str) -> str:
    return hashpw(password.encode(), gensalt()).decode()

def check_password(password: str, hashed: str) -> bool:
    return checkpw(password.encode(), hashed.encode())