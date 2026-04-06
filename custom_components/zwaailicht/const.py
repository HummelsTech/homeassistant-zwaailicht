"""Constants for the Zwaailicht P2000 integration."""

DOMAIN = "zwaailicht"
DEFAULT_SCAN_INTERVAL = 60  # seconds
MIN_SCAN_INTERVAL = 30
FEED_URL_TEMPLATE = "https://zwaailicht.nu/feed/meldingen/{stad}.xml"

CONF_STAD = "stad"
CONF_SCAN_INTERVAL = "scan_interval"

DIENST_ICONS: dict[str, str] = {
    "brandweer": "mdi:fire-truck",
    "ambulance": "mdi:ambulance",
    "politie": "mdi:police-badge",
    "knrm": "mdi:lifebuoy",
}
DEFAULT_ICON = "mdi:alert-circle"

# Mappings to detect dienst from title emoji or keywords (fallback if
# category tags are missing).
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
