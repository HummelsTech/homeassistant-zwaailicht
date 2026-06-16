"""DataUpdateCoordinator for Zwaailicht P2000."""

from __future__ import annotations

from datetime import timedelta
import logging
import re
from typing import Any

import feedparser

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    DIENST_EMOJI_MAP,
    DIENST_KEYWORD_MAP,
    DOMAIN,
    haversine,
)

_LOGGER = logging.getLogger(__name__)

# Pattern to extract priority code and label from meldingen titles.
# Examples: "🚑 A1 Spoed — Brouwersgracht, Amsterdam"
#           "🔥 P2 Urgent — Saaftingestraat, Amsterdam"
_MELDINGEN_TITLE_RE = re.compile(
    r"^.+?\s+([A-Z]\d)\s+(.+?)\s+[—\-]\s+(.+),\s*(.+)$"
)

# Pattern to extract structured fields from meldingen summary.
# Example: "Brandweer melding. Prioriteit: Urgent. Eenheid: BAD-01. Type: Brand."
_SUMMARY_FIELD_RE = re.compile(r"(\w[\w\s]*?):\s*([^.]+)")


class ZwaailichtCoordinator(DataUpdateCoordinator[list[dict[str, Any]]]):
    """Coordinator that polls a zwaailicht.nu Atom feed."""

    def __init__(
        self,
        hass: HomeAssistant,
        *,
        feed_url: str,
        feed_type: str,
        scan_interval: int,
        radius_km: float,
    ) -> None:
        """Initialize the coordinator."""
        self.feed_url = feed_url
        self.feed_type = feed_type
        self.radius_km = radius_km

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{feed_type}",
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
                f"Error fetching feed {self.feed_url}: {err}"
            ) from err

        if resp.status == 304:
            return self._previous_data

        if resp.status != 200:
            raise UpdateFailed(
                f"Feed returned HTTP {resp.status} for {self.feed_url}"
            )

        self._etag = resp.headers.get("ETag")
        self._last_modified = resp.headers.get("Last-Modified")

        body = await resp.text()
        feed = await self.hass.async_add_executor_job(feedparser.parse, body)

        entries = self._process_entries(feed.entries)
        self._fire_new_events(entries)
        self._previous_data = entries
        return entries

    def _process_entries(
        self, raw_entries: list[Any]
    ) -> list[dict[str, Any]]:
        """Convert feed entries to normalized dicts, filter by radius."""
        home_lat = self.hass.config.latitude
        home_lon = self.hass.config.longitude
        has_home = home_lat is not None and home_lon is not None

        if not has_home:
            _LOGGER.warning(
                "Home location not set in HA — cannot filter by distance, "
                "including all entries"
            )

        results: list[dict[str, Any]] = []

        for entry in raw_entries:
            entry_id = getattr(entry, "id", None) or getattr(
                entry, "link", ""
            )

            title = getattr(entry, "title", "")
            summary = getattr(entry, "summary", "")

            # Extract dienst and city from category tags.
            dienst = ""
            stad = ""
            tags = getattr(entry, "tags", [])
            for tag in tags:
                term = tag.get("term", "").lower()
                if term in (
                    "ambulance", "brandweer", "politie", "knrm", "piek",
                ):
                    dienst = term
                else:
                    stad = term
            if not dienst:
                dienst = _detect_dienst(title) or _detect_dienst(summary)

            # Build the core alert dict.
            alert: dict[str, Any] = {
                "id": entry_id,
                "title": title,
                "timestamp": getattr(entry, "updated", "")
                or getattr(entry, "published", ""),
                "link": getattr(entry, "link", ""),
                "dienst": dienst,
                "stad": stad,
            }

            # Parse georss:point → latitude, longitude, distance_km.
            lat, lon = _parse_georss_point(entry)
            has_geo = lat is not None and lon is not None
            if has_geo:
                alert["latitude"] = lat
                alert["longitude"] = lon
                if has_home:
                    dist = haversine(home_lat, home_lon, lat, lon)
                    alert["distance_km"] = round(dist, 1)

            # Radius filtering — meldingen only. Pieken are national
            # curated incidents and always included regardless of distance.
            if self.feed_type == "meldingen" and has_home:
                dist = alert.get("distance_km")
                if dist is not None and dist > self.radius_km:
                    continue
                if dist is None:
                    # Can't determine proximity without geo data.
                    continue

            # Meldingen-specific: parse priority and structured summary.
            if self.feed_type == "meldingen":
                m = _MELDINGEN_TITLE_RE.match(title)
                if m:
                    alert["prioriteit_code"] = m.group(1)
                    alert["prioriteit"] = m.group(2)
                    alert["locatie"] = m.group(3).strip()

                if summary:
                    alert["summary"] = summary
                    for field_match in _SUMMARY_FIELD_RE.finditer(summary):
                        key = field_match.group(1).strip().lower()
                        value = field_match.group(2).strip()
                        if key == "eenheid":
                            alert["eenheid"] = value
                        elif key == "type":
                            alert["type"] = value
            else:
                # Pieken: summary is the full incident description.
                if summary:
                    alert["summary"] = summary

            results.append(alert)

        return results

    def _fire_new_events(
        self, entries: list[dict[str, Any]]
    ) -> None:
        """Fire HA events for entries not seen in the previous poll."""
        event_type = (
            "zwaailicht_new_piek"
            if self.feed_type == "pieken"
            else "zwaailicht_new_alert"
        )
        for alert in entries:
            alert_id = alert["id"]
            if alert_id not in self._seen_ids:
                self._seen_ids.add(alert_id)
                self.hass.bus.async_fire(event_type, dict(alert))

        # Trim seen_ids to prevent unbounded growth.
        if len(self._seen_ids) > 500:
            current_ids = {e["id"] for e in entries}
            self._seen_ids = current_ids


def _parse_georss_point(entry: Any) -> tuple[float | None, float | None]:
    """Extract lat/lon from a georss:point element.

    feedparser exposes <georss:point> as entry.where with GeoJSON-ordered
    coordinates (lon, lat), not as entry.georss_point.
    """
    where = getattr(entry, "where", None)
    if isinstance(where, dict):
        coords = where.get("coordinates")
        if coords and len(coords) == 2:
            try:
                lon, lat = float(coords[0]), float(coords[1])
                return lat, lon
            except (TypeError, ValueError):
                pass
    point = getattr(entry, "georss_point", None)
    if point:
        parts = point.split()
        if len(parts) == 2:
            try:
                return float(parts[0]), float(parts[1])
            except ValueError:
                pass
    return None, None


def _detect_dienst(text: str) -> str:
    """Detect dienst from emoji prefix or keywords in text."""
    for emoji, dienst in DIENST_EMOJI_MAP.items():
        if emoji in text:
            return dienst
    text_lower = text.lower()
    for keyword, dienst in DIENST_KEYWORD_MAP.items():
        if keyword in text_lower:
            return dienst
    return ""
