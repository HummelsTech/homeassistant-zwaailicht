"""Constants for the Zwaailicht P2000 integration."""

from math import asin, cos, radians, sin, sqrt

DOMAIN = "zwaailicht"
DEFAULT_SCAN_INTERVAL = 60  # seconds
MIN_SCAN_INTERVAL = 30
DEFAULT_RADIUS_KM = 10.0

MELDINGEN_URL = "https://zwaailicht.nu/feed/meldingen.xml"
PIEKEN_URL = "https://zwaailicht.nu/feed/pieken.xml"

CONF_RADIUS_KM = "radius_km"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_PIEKEN = "pieken"
CONF_SIGNIFICANT = "significant_only"

DIENST_ICONS: dict[str, str] = {
    "brandweer": "mdi:fire-truck",
    "ambulance": "mdi:ambulance",
    "politie": "mdi:police-badge",
    "knrm": "mdi:lifebuoy",
    "piek": "mdi:alert-octagon",
}
DEFAULT_ICON = "mdi:alert-circle"

# Fallback mappings to detect dienst from title emoji or keywords.
DIENST_EMOJI_MAP: dict[str, str] = {
    "\U0001f525": "brandweer",   # 🔥
    "\U0001f692": "brandweer",   # 🚒
    "\U0001f691": "ambulance",   # 🚑
    "\U0001f693": "politie",     # 🚓
    "\U0001f6df": "knrm",        # 🛟
    "\u26f5": "knrm",            # ⛵
}
DIENST_KEYWORD_MAP: dict[str, str] = {
    "brandweer": "brandweer",
    "ambulance": "ambulance",
    "politie": "politie",
    "knrm": "knrm",
    "reddingsbrigade": "knrm",
}

EARTH_RADIUS_KM = 6371.0


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance in km between two points."""
    lat1, lon1, lat2, lon2 = map(radians, (lat1, lon1, lat2, lon2))
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_KM * asin(sqrt(a))
