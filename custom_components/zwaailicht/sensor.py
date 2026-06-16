"""Sensor platform for Zwaailicht P2000."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEFAULT_ICON, DIENST_ICONS, DOMAIN
from .coordinator import ZwaailichtCoordinator


def _device_info(entry: ConfigEntry) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name="Zwaailicht P2000",
        manufacturer="zwaailicht.nu",
        entry_type=DeviceEntryType.SERVICE,
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Zwaailicht sensors from a config entry."""
    coordinators: dict[str, ZwaailichtCoordinator] = hass.data[DOMAIN][
        entry.entry_id
    ]
    device = _device_info(entry)
    entities: list[SensorEntity] = []

    meldingen = coordinators["meldingen"]
    entities.append(LaatsteAlertSensor(meldingen, device, entry.entry_id))
    entities.append(AlertCountSensor(meldingen, device, entry.entry_id))

    if "pieken" in coordinators:
        entities.append(LaatstePiekSensor(coordinators["pieken"], device, entry.entry_id))

    async_add_entities(entities)


class LaatsteAlertSensor(
    CoordinatorEntity[ZwaailichtCoordinator], SensorEntity
):
    """The most recent P2000 alert within radius."""

    _attr_has_entity_name = True
    _attr_name = "Laatste melding"

    def __init__(
        self, coordinator: ZwaailichtCoordinator, device: DeviceInfo, entry_id: str
    ) -> None:
        super().__init__(coordinator)
        self._attr_device_info = device
        self._attr_unique_id = f"{entry_id}_laatste_melding"

    @property
    def _latest(self) -> dict[str, Any] | None:
        data = self.coordinator.data
        return data[0] if data else None

    @property
    def native_value(self) -> str:
        latest = self._latest
        if latest is None:
            return "Geen meldingen"
        title = latest.get("title", "")
        return title[:255] if len(title) > 255 else title

    @property
    def icon(self) -> str:
        latest = self._latest
        if latest is None:
            return DEFAULT_ICON
        return DIENST_ICONS.get(latest.get("dienst", ""), DEFAULT_ICON)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        latest = self._latest
        if latest is None:
            return {}
        attrs: dict[str, Any] = {}
        for key in (
            "dienst", "stad", "timestamp", "link",
            "prioriteit_code", "prioriteit", "locatie",
            "distance_km",
        ):
            if key in latest:
                attrs[key] = latest[key]
        return attrs


class AlertCountSensor(
    CoordinatorEntity[ZwaailichtCoordinator], SensorEntity
):
    """Number of recent alerts within radius."""

    _attr_has_entity_name = True
    _attr_name = "Aantal meldingen"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:counter"

    def __init__(
        self, coordinator: ZwaailichtCoordinator, device: DeviceInfo, entry_id: str
    ) -> None:
        super().__init__(coordinator)
        self._attr_device_info = device
        self._attr_unique_id = f"{entry_id}_aantal_meldingen"

    @property
    def native_value(self) -> int:
        data = self.coordinator.data
        return len(data) if data else 0


class LaatstePiekSensor(
    CoordinatorEntity[ZwaailichtCoordinator], SensorEntity
):
    """The most recent national piek."""

    _attr_has_entity_name = True
    _attr_name = "Laatste piek"
    _attr_icon = "mdi:alert-octagon"

    def __init__(
        self, coordinator: ZwaailichtCoordinator, device: DeviceInfo, entry_id: str
    ) -> None:
        super().__init__(coordinator)
        self._attr_device_info = device
        self._attr_unique_id = f"{entry_id}_laatste_piek"

    @property
    def _latest(self) -> dict[str, Any] | None:
        data = self.coordinator.data
        return data[0] if data else None

    @property
    def native_value(self) -> str:
        latest = self._latest
        if latest is None:
            return "Geen pieken"
        title = latest.get("title", "")
        return title[:255] if len(title) > 255 else title

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        latest = self._latest
        if latest is None:
            return {}
        attrs: dict[str, Any] = {}
        for key in ("stad", "timestamp", "link", "summary", "distance_km"):
            if key in latest:
                attrs[key] = latest[key]
        return attrs
