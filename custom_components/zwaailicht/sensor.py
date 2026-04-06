"""Sensor platform for Zwaailicht P2000."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_STAD, DEFAULT_ICON, DIENST_ICONS, DOMAIN
from .coordinator import ZwaailichtCoordinator

MAX_RECENT_ALERTS = 10


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Zwaailicht sensor from a config entry."""
    coordinator: ZwaailichtCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ZwaailichtSensor(coordinator, entry)])


class ZwaailichtSensor(
    CoordinatorEntity[ZwaailichtCoordinator], SensorEntity
):
    """Sensor representing the latest P2000 alert for a city."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ZwaailichtCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        stad = entry.data[CONF_STAD]
        self._attr_unique_id = f"zwaailicht_{stad}"
        self._attr_name = f"Zwaailicht {stad.title()}"
        self._attr_translation_key = "zwaailicht"

    @property
    def _latest(self) -> dict[str, Any] | None:
        """Return the most recent alert, if any."""
        data = self.coordinator.data
        if data:
            return data[0]
        return None

    @property
    def native_value(self) -> str | None:
        """Return the title of the most recent alert."""
        latest = self._latest
        if latest is None:
            return None
        title = latest.get("title", "")
        return title[:255] if len(title) > 255 else title

    @property
    def icon(self) -> str:
        """Return an icon based on the dienst of the latest alert."""
        latest = self._latest
        if latest is None:
            return DEFAULT_ICON
        dienst = latest.get("dienst", "")
        return DIENST_ICONS.get(dienst, DEFAULT_ICON)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return attributes from the latest alert plus recent alerts list."""
        latest = self._latest
        if latest is None:
            return {}

        attrs: dict[str, Any] = {
            "dienst": latest.get("dienst"),
            "timestamp": latest.get("timestamp"),
            "link": latest.get("link"),
        }

        for key in ("capcode", "latitude", "longitude", "distance_km", "piek_url"):
            if key in latest:
                attrs[key] = latest[key]

        data = self.coordinator.data or []
        attrs["recent_alerts"] = data[:MAX_RECENT_ALERTS]

        return attrs
