"""Config flow for Zwaailicht P2000 integration."""

from __future__ import annotations

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_FEED_TYPE,
    CONF_MAX_DISTANCE_KM,
    CONF_SCAN_INTERVAL,
    CONF_STAD,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    FEED_TYPE_MELDINGEN,
    FEED_TYPE_PIEKEN,
    MELDINGEN_URL_TEMPLATE,
    MIN_SCAN_INTERVAL,
    PIEKEN_URL,
)

STEP_MELDINGEN_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_STAD): str,
    }
)

STEP_OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Optional(
            CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
        ): vol.All(int, vol.Range(min=MIN_SCAN_INTERVAL)),
        vol.Optional(CONF_MAX_DISTANCE_KM): vol.All(
            vol.Coerce(float), vol.Range(min=0.1)
        ),
    }
)


class ZwaailichtConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Zwaailicht P2000."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize."""
        self._feed_type: str = ""
        self._stad: str = ""

    async def async_step_user(
        self, user_input: dict[str, str] | None = None
    ) -> ConfigFlowResult:
        """Show menu: meldingen (per city) or pieken (national)."""
        return self.async_show_menu(
            step_id="user",
            menu_options=["meldingen", "pieken"],
        )

    async def async_step_meldingen(
        self, user_input: dict[str, str] | None = None
    ) -> ConfigFlowResult:
        """Handle city input for meldingen feed."""
        errors: dict[str, str] = {}

        if user_input is not None:
            stad = user_input[CONF_STAD].strip().lower()

            await self.async_set_unique_id(f"meldingen_{stad}")
            self._abort_if_unique_id_configured()

            url = MELDINGEN_URL_TEMPLATE.format(stad=stad)
            session = async_get_clientsession(self.hass)
            try:
                resp = await session.get(url, timeout=10)
                if resp.status == 200:
                    self._feed_type = FEED_TYPE_MELDINGEN
                    self._stad = stad
                    return await self.async_step_options()
                errors["base"] = "stad_not_found"
            except Exception:  # noqa: BLE001
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="meldingen",
            data_schema=STEP_MELDINGEN_SCHEMA,
            errors=errors,
        )

    async def async_step_pieken(
        self, user_input: dict[str, str] | None = None
    ) -> ConfigFlowResult:
        """Handle pieken feed setup (national, no city needed)."""
        await self.async_set_unique_id("pieken")
        self._abort_if_unique_id_configured()

        # Validate that the pieken feed is reachable.
        session = async_get_clientsession(self.hass)
        try:
            resp = await session.get(PIEKEN_URL, timeout=10)
            if resp.status != 200:
                return self.async_abort(reason="cannot_connect")
        except Exception:  # noqa: BLE001
            return self.async_abort(reason="cannot_connect")

        self._feed_type = FEED_TYPE_PIEKEN
        self._stad = ""
        return await self.async_step_options()

    async def async_step_options(
        self, user_input: dict[str, any] | None = None
    ) -> ConfigFlowResult:
        """Handle optional settings (scan interval, distance filter)."""
        if user_input is not None:
            data: dict[str, any] = {
                CONF_FEED_TYPE: self._feed_type,
                CONF_SCAN_INTERVAL: user_input.get(
                    CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                ),
            }
            if self._stad:
                data[CONF_STAD] = self._stad
            max_dist = user_input.get(CONF_MAX_DISTANCE_KM)
            if max_dist is not None:
                data[CONF_MAX_DISTANCE_KM] = max_dist

            if self._feed_type == FEED_TYPE_PIEKEN:
                title = "Zwaailicht Pieken"
            else:
                title = f"Zwaailicht {self._stad.title()}"

            return self.async_create_entry(title=title, data=data)

        return self.async_show_form(
            step_id="options",
            data_schema=STEP_OPTIONS_SCHEMA,
        )
