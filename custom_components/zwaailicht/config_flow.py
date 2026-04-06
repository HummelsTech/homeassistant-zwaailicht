"""Config flow for Zwaailicht P2000 integration."""

from __future__ import annotations

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult

from .const import (
    CONF_PIEKEN,
    CONF_RADIUS_KM,
    CONF_SCAN_INTERVAL,
    DEFAULT_RADIUS_KM,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MIN_SCAN_INTERVAL,
)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_RADIUS_KM, default=DEFAULT_RADIUS_KM): vol.All(
            vol.Coerce(float), vol.Range(min=0.1)
        ),
        vol.Optional(CONF_PIEKEN, default=True): bool,
        vol.Optional(
            CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
        ): vol.All(int, vol.Range(min=MIN_SCAN_INTERVAL)),
    }
)


class ZwaailichtConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Zwaailicht P2000."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, any] | None = None
    ) -> ConfigFlowResult:
        """Single step: radius, pieken toggle, scan interval."""
        # Only one instance allowed.
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            return self.async_create_entry(
                title="Zwaailicht P2000",
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_SCHEMA,
        )
