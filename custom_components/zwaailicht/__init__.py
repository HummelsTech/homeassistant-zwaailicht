"""The Zwaailicht P2000 integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    CONF_MAX_DISTANCE_KM,
    CONF_PIEKEN,
    CONF_SCAN_INTERVAL,
    CONF_STAD,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MELDINGEN_URL_TEMPLATE,
    PIEKEN_URL,
)
from .coordinator import FEED_TYPE_MELDINGEN, FEED_TYPE_PIEKEN, ZwaailichtCoordinator

PLATFORMS = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Zwaailicht P2000 from a config entry."""
    stad = entry.data[CONF_STAD]
    scan_interval = entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    max_distance_km = entry.data.get(CONF_MAX_DISTANCE_KM)

    meldingen_coordinator = ZwaailichtCoordinator(
        hass,
        feed_url=MELDINGEN_URL_TEMPLATE.format(stad=stad),
        feed_type=FEED_TYPE_MELDINGEN,
        stad=stad,
        scan_interval=scan_interval,
        max_distance_km=max_distance_km,
    )
    await meldingen_coordinator.async_config_entry_first_refresh()

    coordinators = {"meldingen": meldingen_coordinator}

    if entry.data.get(CONF_PIEKEN, False):
        pieken_coordinator = ZwaailichtCoordinator(
            hass,
            feed_url=PIEKEN_URL,
            feed_type=FEED_TYPE_PIEKEN,
            stad=stad,
            scan_interval=scan_interval,
            max_distance_km=max_distance_km,
        )
        await pieken_coordinator.async_config_entry_first_refresh()
        coordinators["pieken"] = pieken_coordinator

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinators

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, PLATFORMS
    )
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
