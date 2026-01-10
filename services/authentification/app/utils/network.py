import ipaddress
import json
import logging
from dadata import Dadata
from user_agents import parse as ua_parse

logger = logging.getLogger(__name__)

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

def get_location(ip: str, dadata_client: Dadata | None) -> dict:
    """Получает местоположение по IP-адресу через DaData."""
    try:
        ip_obj = ipaddress.ip_address(ip)
        if ip_obj.is_private or ip_obj.is_loopback:
             return {
                "country": None, 
                "city": None, 
                "full": "Local Network"
            }
    except ValueError:
        pass 

    if not dadata_client:
        return {"country": None, "city": None, "full": "Unknown"}

    try:
        response = dadata_client.iplocate(ip)
        
        if not response:
             return {"country": None, "city": None, "full": "Unknown"}

        data = response.get("data")
        
        if not data:
            logger.warning(f"DaData returned response without 'data' block for {ip}")
            return {"country": None, "city": None, "full": "Unknown"}
            
        country = data.get("country", "Unknown")
        city = data.get("city")

        if not city:
            city = data.get("region_with_type") or data.get("region") or "Unknown"

        full_location = f"{country}, {city}"

        return {
            "country": country,
            "city": city,
            "full": full_location
        }

    except Exception as e:
        logger.error(f"DaData lookup error for IP {ip}: {e}", exc_info=True)
        return {"country": None, "city": None, "full": "Unknown"}