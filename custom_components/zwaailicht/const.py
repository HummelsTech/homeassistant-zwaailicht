"""Constants for the Zwaailicht P2000 integration."""

from math import asin, cos, radians, sin, sqrt

DOMAIN = "zwaailicht"
DEFAULT_SCAN_INTERVAL = 60  # seconds
MIN_SCAN_INTERVAL = 30
FEED_URL_TEMPLATE = "https://zwaailicht.nu/feeds/{stad}.xml"
DEFAULT_MAX_DISTANCE_KM = None  # None = no filtering

CONF_STAD = "stad"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_MAX_DISTANCE_KM = "max_distance_km"

DIENST_ICONS: dict[str, str] = {
    "brandweer": "mdi:fire-truck",
    "ambulance": "mdi:ambulance",
    "politie": "mdi:police-badge",
    "knrm": "mdi:lifebuoy",
}
DEFAULT_ICON = "mdi:alert-circle"

EARTH_RADIUS_KM = 6371.0


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance in km between two points."""
    lat1, lon1, lat2, lon2 = map(radians, (lat1, lon1, lat2, lon2))
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_KM * asin(sqrt(a))
