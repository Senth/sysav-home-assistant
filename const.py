from __future__ import annotations
from homeassistant.const import Platform

DOMAIN = "sysav_next"
PLATFORMS: list[Platform] = [Platform.SENSOR]

DEFAULT_SCAN_INTERVAL_MINUTES = 6 * 60  # var 6:e timme

SUPPORTED_MUNICIPALITIES = {
    "kavlinge": "Kävlinge",
    "lomma": "Lomma",
    "svedala": "Svedala",
}

CONF_MUNICIPALITY = "municipality"
CONF_STREET = "street"
CONF_NUMBER = "number"
CONF_CITY = "city"  # Postort/by (t.ex. Bjärred)
CONF_API_BASE = "api_base"
CONF_LABELS = "labels"

# Default-mappning för kärlnamn som förekommer i olika kommuner
DEFAULT_LABELS = {
    "karl_1": ["Kärl 1", "Restavfall", "Restavfall (Kärl 1)"],
    "karl_2": ["Kärl 2", "Matavfall", "Matavfall (Kärl 2)"],
}

SENSOR_DESCRIPTIONS = {
    "karl_1": {
        "name": "Kärl 1 – nästa tömning",
        "icon": "mdi:trash-can",
    },
    "karl_2": {
        "name": "Kärl 2 – nästa tömning",
        "icon": "mdi:food-apple",
    },
}
