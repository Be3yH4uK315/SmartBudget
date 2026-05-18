import ipaddress
import logging
from dataclasses import dataclass

from dadata import Dadata
from user_agents import parse as parse_user_agent

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LocationData:
    """Данные о местоположении пользователя."""

    country: str | None
    city: str | None
    full: str


def parse_device(user_agent: str) -> str:
    """Извлекает краткое описание устройства из User-Agent."""
    try:
        parsed_ua = parse_user_agent(user_agent)

        device_family = parsed_ua.device.family or "Unknown"
        os_family = parsed_ua.os.family or "Unknown"
        os_version = parsed_ua.os.version_string or ""

        device = f"{device_family}, {os_family}"
        if os_version:
            device = f"{device} {os_version}"

        return device[:255]

    except Exception as exc:
        logger.warning("Failed to parse User-Agent: %s", exc, exc_info=True)
        return "Unknown Device"


def get_location(ip: str, dadata_client: Dadata | None) -> LocationData:
    """Получает местоположение по IP-адресу через DaData."""
    unknown_location = LocationData(None, None, "Unknown")
    local_location = LocationData(None, None, "Local Network")

    try:
        ip_obj = ipaddress.ip_address(ip)
        if ip_obj.is_private or ip_obj.is_loopback:
            return local_location
    except ValueError:
        logger.warning("Invalid IP address for location lookup: %s", ip)
        return unknown_location

    if dadata_client is None:
        logger.warning("DaData location lookup skipped for IP %s: client is missing", ip)
        return unknown_location

    try:
        response = dadata_client.iplocate(ip)
        if not response:
            logger.warning("DaData returned empty response for IP %s", ip)
            return unknown_location

        data = response.get("data")
        if not data:
            logger.warning("DaData response has no data block for IP %s", ip)
            return unknown_location

        country = data.get("country") or "Unknown"
        city = data.get("city") or data.get("region_with_type") or data.get("region")

        if not city:
            city = "Unknown"

        return LocationData(
            country=country,
            city=city,
            full=f"{country}, {city}",
        )

    except Exception as exc:
        logger.error(
            "DaData lookup error for IP %s: %s",
            ip,
            exc,
            exc_info=True,
        )
        return unknown_location
