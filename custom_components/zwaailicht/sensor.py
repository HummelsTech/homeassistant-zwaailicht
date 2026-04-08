"""Sensor platform for Zwaailicht P2000."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEFAULT_ICON, DIENST_ICONS, DOMAIN
from .coordinator import ZwaailichtCoordinator

MAX_RECENT = 10


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Zwaailicht sensors from a config entry."""
    coordinators: dict[str, ZwaailichtCoordinator] = hass.data[DOMAIN][
        entry.entry_id
    ]
    entities: list[ZwaailichtSensor] = []

    entities.append(
        ZwaailichtSensor(
            coordinators["meldingen"],
            entry=entry,
            unique_id="zwaailicht_meldingen",
            name="Meldingen",
        )
    )

    if "pieken" in coordinators:
        entities.append(
            ZwaailichtSensor(
                coordinators["pieken"],
                entry=entry,
                unique_id="zwaailicht_pieken",
                name="Pieken",
                recent_key="recent_pieken",
            )
        )

    async_add_entities(entities)


class ZwaailichtSensor(
    CoordinatorEntity[ZwaailichtCoordinator], SensorEntity
):
    """Sensor representing the latest P2000 alert or piek within radius."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ZwaailichtCoordinator,
        *,
        entry: ConfigEntry,
        unique_id: str,
        name: str,
        recent_key: str = "recent_alerts",
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = unique_id
        self._attr_name = name
        self._recent_key = recent_key
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Zwaailicht P2000",
            manufacturer="zwaailicht.nu",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def _latest(self) -> dict[str, Any] | None:
        """Return the most recent entry, if any."""
        data = self.coordinator.data
        if data:
            return data[0]
        return None

    @property
    def native_value(self) -> str | None:
        """Return the title of the most recent entry."""
        latest = self._latest
        if latest is None:
            return None
        title = latest.get("title", "")
        return title[:255] if len(title) > 255 else title

    @property
    def icon(self) -> str:
        """Return an icon based on the dienst of the latest entry."""
        latest = self._latest
        if latest is None:
            return DEFAULT_ICON
        dienst = latest.get("dienst", "")
        return DIENST_ICONS.get(dienst, DEFAULT_ICON)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return attributes from the latest entry plus recent entries list."""
        latest = self._latest
        if latest is None:
            return {}

        attrs: dict[str, Any] = {
            "dienst": latest.get("dienst"),
            "timestamp": latest.get("timestamp"),
            "link": latest.get("link"),
            "stad": latest.get("stad"),
        }

        for key in (
            "prioriteit_code", "prioriteit", "locatie",
            "summary", "eenheid", "type",
            "latitude", "longitude", "distance_km",
        ):
            if key in latest:
                attrs[key] = latest[key]

        data = self.coordinator.data or []
        attrs[self._recent_key] = data[:MAX_RECENT]

        return attrs
