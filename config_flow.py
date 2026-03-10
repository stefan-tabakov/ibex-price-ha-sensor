"""Config flow for IBEX Price integration."""
from __future__ import annotations

import re
from urllib.parse import urlparse

import pytz
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
        # Check if config entry already exists
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        
        errors = {}
        
        if user_input is not None:
            # Validate timezone
            timezone = user_input.get(CONF_TIMEZONE, DEFAULT_TIMEZONE)
            try:
                pytz.timezone(timezone)
            except pytz.UnknownTimeZoneError:
                errors[CONF_TIMEZONE] = "invalid_timezone"
            
            # Validate API endpoint URL
            api_endpoint = user_input.get(CONF_API_ENDPOINT, DEFAULT_API_ENDPOINT)
            try:
                parsed = urlparse(api_endpoint)
                if not all([parsed.scheme, parsed.netloc]) or parsed.scheme not in ['http', 'https']:
                    errors[CONF_API_ENDPOINT] = "invalid_url"
            except Exception:
                errors[CONF_API_ENDPOINT] = "invalid_url"
            
            # Validate scan interval
            scan_interval = user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
            if not isinstance(scan_interval, int) or scan_interval < 60:
                errors[CONF_SCAN_INTERVAL] = "invalid_interval"
            
            if not errors:
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
            errors=errors,
        )
