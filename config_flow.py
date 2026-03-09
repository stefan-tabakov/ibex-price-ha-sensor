"""Config flow for IBEX Price integration."""
from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN, 
    DEFAULT_SCAN_INTERVAL, 
    DEFAULT_TIMEZONE, 
    DEFAULT_API_ENDPOINT,
    CONF_TIMEZONE,
    CONF_API_ENDPOINT
)


class IbexPriceConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for IBEX Price."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, str] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is not None:
            return self.async_create_entry(
                title="IBEX Price Sensor",
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SCAN_INTERVAL, 
                        default=DEFAULT_SCAN_INTERVAL
                    ): vol.All(vol.Coerce(int), vol.Range(min=60)),
                    vol.Optional(CONF_TIMEZONE, default=DEFAULT_TIMEZONE): vol.Coerce(str),
                    vol.Optional(CONF_API_ENDPOINT, default=DEFAULT_API_ENDPOINT): vol.Coerce(str),
                }
            ),
        )
