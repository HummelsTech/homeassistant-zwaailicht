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
    CONF_SCAN_INTERVAL,
    CONF_STAD,
    DEFAULT_SCAN_INTERVAL,
    DIENST_EMOJI_MAP,
    DIENST_KEYWORD_MAP,
    DOMAIN,
    FEED_URL_TEMPLATE,
)

_LOGGER = logging.getLogger(__name__)

# Pattern to extract priority code and label from title.
# Examples: "🚑 A1 Spoed — Brouwersgracht, Amsterdam"
#           "🔥 P2 Urgent — Saaftingestraat, Amsterdam"
_TITLE_RE = re.compile(
    r"^.+?\s+([A-Z]\d)\s+(.+?)\s+[—\-]\s+(.+),\s*(.+)$"
)

# Pattern to extract structured fields from summary.
# Example: "Brandweer melding. Prioriteit: Urgent. Eenheid: BAD-01. Type: Brand."
_SUMMARY_FIELD_RE = re.compile(r"(\w[\w\s]*?):\s*([^.]+)")


class ZwaailichtCoordinator(DataUpdateCoordinator[list[dict[str, Any]]]):
    """Coordinator that polls a zwaailicht.nu Atom feed."""

    def __init__(self, hass: HomeAssistant, config: dict[str, Any]) -> None:
        """Initialize the coordinator."""
        self.stad: str = config[CONF_STAD]
        self.feed_url: str = FEED_URL_TEMPLATE.format(stad=self.stad)

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
        """Convert feed entries to normalized dicts."""
        results: list[dict[str, Any]] = []

        for entry in raw_entries:
            entry_id = getattr(entry, "id", None) or getattr(
                entry, "link", ""
            )

            title = getattr(entry, "title", "")
            summary = getattr(entry, "summary", "")

            # Extract dienst from category tags (primary), fall back to
            # emoji / keyword detection.
            dienst = ""
            tags = getattr(entry, "tags", [])
            if tags:
                dienst = tags[0].get("term", "").lower()
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
                "stad": self.stad,
            }

            # Parse structured fields from title.
            # "🚑 A1 Spoed — Brouwersgracht, Amsterdam"
            m = _TITLE_RE.match(title)
            if m:
                alert["prioriteit_code"] = m.group(1)   # e.g. "A1"
                alert["prioriteit"] = m.group(2)         # e.g. "Spoed"
                alert["locatie"] = m.group(3).strip()    # e.g. "Brouwersgracht"

            # Parse structured fields from summary.
            # "Brandweer melding. Prioriteit: Urgent. Eenheid: BAD-01. Type: Brand."
            if summary:
                alert["summary"] = summary
                for field_match in _SUMMARY_FIELD_RE.finditer(summary):
                    key = field_match.group(1).strip().lower()
                    value = field_match.group(2).strip()
                    if key == "eenheid":
                        alert["eenheid"] = value
                    elif key == "type":
                        alert["type"] = value

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
            current_ids = {e["id"] for e in entries}
            self._seen_ids = current_ids


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
