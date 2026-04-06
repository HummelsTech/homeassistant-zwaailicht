"""Config flow for Zwaailicht P2000 integration."""

from __future__ import annotations

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback

from .const import (
    CONF_PIEKEN,
    CONF_RADIUS_KM,
    CONF_SCAN_INTERVAL,
    CONF_SIGNIFICANT,
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
        vol.Optional(CONF_SIGNIFICANT, default=True): bool,
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

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Return the options flow handler."""
        return ZwaailichtOptionsFlow(config_entry)


class ZwaailichtOptionsFlow(OptionsFlow):
    """Handle options for Zwaailicht P2000."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, any] | None = None
    ) -> ConfigFlowResult:
        """Manage options."""
        if user_input is not None:
            # Write new values back to data (not options) and reload.
            self.hass.config_entries.async_update_entry(
                self._config_entry, data=user_input
            )
            await self.hass.config_entries.async_reload(
                self._config_entry.entry_id
            )
            return self.async_create_entry(title="", data={})

        current = self._config_entry.data
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_RADIUS_KM,
                        default=current.get(CONF_RADIUS_KM, DEFAULT_RADIUS_KM),
                    ): vol.All(vol.Coerce(float), vol.Range(min=0.1)),
                    vol.Optional(
                        CONF_SIGNIFICANT,
                        default=current.get(CONF_SIGNIFICANT, True),
                    ): bool,
                    vol.Optional(
                        CONF_PIEKEN,
                        default=current.get(CONF_PIEKEN, True),
                    ): bool,
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=current.get(
                            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                        ),
                    ): vol.All(int, vol.Range(min=MIN_SCAN_INTERVAL)),
                }
            ),
        )
