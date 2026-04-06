"""DataUpdateCoordinator for Zwaailicht P2000."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

import feedparser

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    CONF_MAX_DISTANCE_KM,
    CONF_SCAN_INTERVAL,
    CONF_STAD,
    DEFAULT_MAX_DISTANCE_KM,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    FEED_URL_TEMPLATE,
    haversine,
)

_LOGGER = logging.getLogger(__name__)


class ZwaailichtCoordinator(DataUpdateCoordinator[list[dict[str, Any]]]):
    """Coordinator that polls a zwaailicht.nu Atom feed."""

    def __init__(self, hass: HomeAssistant, config: dict[str, Any]) -> None:
        """Initialize the coordinator."""
        self.stad: str = config[CONF_STAD]
        self.feed_url: str = FEED_URL_TEMPLATE.format(stad=self.stad)
        self.max_distance_km: float | None = config.get(
            CONF_MAX_DISTANCE_KM, DEFAULT_MAX_DISTANCE_KM
        )

        scan_interval = config.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{self.stad}",
            update_interval=timedelta(seconds=scan_interval),
        )

        self._etag: str | None = None
        self._last_modified: str | None = None
        self._seen_ids: set[str] = set()
        self._previous_data: list[dict[str, Any]] = []

    async def _async_update_data(self) -> list[dict[str, Any]]:
        """Fetch and parse the Atom feed."""
        session = async_get_clientsession(self.hass)
        headers: dict[str, str] = {}
        if self._etag:
            headers["If-None-Match"] = self._etag
        if self._last_modified:
            headers["If-Modified-Since"] = self._last_modified

        try:
            resp = await session.get(
                self.feed_url, headers=headers, timeout=15
            )
        except Exception as err:
            raise UpdateFailed(
                f"Error fetching feed for {self.stad}: {err}"
            ) from err

        if resp.status == 304:
            return self._previous_data

        if resp.status != 200:
            raise UpdateFailed(
                f"Feed returned HTTP {resp.status} for {self.stad}"
            )

        self._etag = resp.headers.get("ETag")
        self._last_modified = resp.headers.get("Last-Modified")

        body = await resp.text()
        feed = await self.hass.async_add_executor_job(feedparser.parse, body)

        entries = self._process_entries(feed.entries)
        self._fire_new_alert_events(entries)
        self._previous_data = entries
        return entries

    def _process_entries(
        self, raw_entries: list
    ) -> list[dict[str, Any]]:
        """Convert feed entries to normalized dicts and apply filters."""
        results: list[dict[str, Any]] = []

        for entry in raw_entries:
            entry_id = getattr(entry, "id", None) or getattr(
                entry, "link", ""
            )

            # Extract dienst from categories/tags.
            dienst = ""
            tags = getattr(entry, "tags", [])
            if tags:
                dienst = tags[0].get("term", "").lower()

            # Build the alert dict.
            alert: dict[str, Any] = {
                "id": entry_id,
                "title": getattr(entry, "title", ""),
                "timestamp": getattr(entry, "updated", "")
                or getattr(entry, "published", ""),
                "link": getattr(entry, "link", ""),
                "dienst": dienst,
                "stad": self.stad,
            }

            # Optional fields: capcode, lat/lon, piek.
            summary = getattr(entry, "summary", "")
            content_list = getattr(entry, "content", [])
            content_text = (
                content_list[0].get("value", "") if content_list else ""
            )

            # Try to extract capcode from title or summary.
            for text in (entry.get("title", ""), summary, content_text):
                if not text:
                    continue
                # Common pattern: capcode in parentheses or as a field.
                # We store raw if found in structured fields.

            # Geo fields — check georss or geo namespace.
            lat = _get_float(entry, "geo_lat") or _get_float(
                entry, "georss_point_lat"
            )
            lon = _get_float(entry, "geo_long") or _get_float(
                entry, "georss_point_lon"
            )

            # Also handle georss:point "lat lon" format.
            if lat is None and hasattr(entry, "georss_point"):
                parts = entry.georss_point.split()
                if len(parts) == 2:
                    try:
                        lat, lon = float(parts[0]), float(parts[1])
                    except ValueError:
                        pass

            if lat is not None and lon is not None:
                alert["latitude"] = lat
                alert["longitude"] = lon
                # Always compute distance if home location is set.
                if (
                    self.hass.config.latitude is not None
                    and self.hass.config.longitude is not None
                ):
                    dist = haversine(
                        self.hass.config.latitude,
                        self.hass.config.longitude,
                        lat,
                        lon,
                    )
                    alert["distance_km"] = round(dist, 1)

            # Extract capcode if present as a custom field.
            capcode = getattr(entry, "capcode", None)
            if capcode:
                alert["capcode"] = capcode

            # Piek URL — look for an alternate link or custom field.
            for link_entry in getattr(entry, "links", []):
                if link_entry.get("rel") == "related":
                    alert["piek_url"] = link_entry["href"]
                    break

            # Proximity filtering.
            if self.max_distance_km is not None:
                dist = alert.get("distance_km")
                if dist is not None and dist > self.max_distance_km:
                    continue
                # Entries without lat/lon are always included.

            results.append(alert)

        return results

    def _fire_new_alert_events(
        self, entries: list[dict[str, Any]]
    ) -> None:
        """Fire HA events for entries not seen in the previous poll."""
        for alert in entries:
            alert_id = alert["id"]
            if alert_id not in self._seen_ids:
                self._seen_ids.add(alert_id)
                self.hass.bus.async_fire(
                    "zwaailicht_new_alert", dict(alert)
                )

        # Trim seen_ids to prevent unbounded growth — keep last 500.
        if len(self._seen_ids) > 500:
            # Keep only IDs from current entries.
            current_ids = {e["id"] for e in entries}
            self._seen_ids = current_ids


def _get_float(entry: Any, attr: str) -> float | None:
    """Safely extract a float attribute from a feed entry."""
    val = getattr(entry, attr, None)
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None
