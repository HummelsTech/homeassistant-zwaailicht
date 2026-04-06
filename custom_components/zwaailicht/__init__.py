"""The Zwaailicht P2000 integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    CONF_PIEKEN,
    CONF_RADIUS_KM,
    CONF_SCAN_INTERVAL,
    CONF_SIGNIFICANT,
    DEFAULT_RADIUS_KM,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MELDINGEN_URL,
    PIEKEN_URL,
)
from .coordinator import ZwaailichtCoordinator

PLATFORMS = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Zwaailicht P2000 from a config entry."""
    scan_interval = entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    radius_km = entry.data.get(CONF_RADIUS_KM, DEFAULT_RADIUS_KM)

    meldingen_url = MELDINGEN_URL
    if entry.data.get(CONF_SIGNIFICANT, False):
        meldingen_url += "?filter=significant"

    meldingen = ZwaailichtCoordinator(
        hass,
        feed_url=meldingen_url,
        feed_type="meldingen",
        scan_interval=scan_interval,
        radius_km=radius_km,
    )
    await meldingen.async_config_entry_first_refresh()

    coordinators: dict[str, ZwaailichtCoordinator] = {
        "meldingen": meldingen,
    }

    if entry.data.get(CONF_PIEKEN, False):
        pieken = ZwaailichtCoordinator(
            hass,
            feed_url=PIEKEN_URL,
            feed_type="pieken",
            scan_interval=scan_interval,
            radius_km=radius_km,
        )
        await pieken.async_config_entry_first_refresh()
        coordinators["pieken"] = pieken

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
