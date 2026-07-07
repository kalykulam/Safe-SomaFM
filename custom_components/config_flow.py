"""Config flow for Safe SomaFM."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, NAME


class SafeSomaFMConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Safe SomaFM."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Create the integration; no credentials or settings are required."""
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=vol.Schema({}), errors={})

        return self.async_create_entry(title=NAME, data={})
