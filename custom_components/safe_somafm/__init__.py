"""Safe SomaFM integration for Home Assistant.

Security posture:
- no user credentials
- no dynamic imports
- no shell execution
- no local file reads/writes
- local HTTP endpoints for the optional browser player and dashboard card
- outbound HTTP(S) only to SomaFM for the station catalog, playlists, and streams
"""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .card import async_register_card_view
from .const import DOMAIN
from .player import async_register_player_views
from .panel import async_register_sidebar_panel
from .somafm import SafeSomaFMClient, SomaFMError

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Safe SomaFM from a config entry."""
    session = async_get_clientsession(hass)
    client = SafeSomaFMClient(session)

    try:
        await client.async_get_stations(force_refresh=True)
    except SomaFMError as err:
        # Keep the exact error in Home Assistant logs while preserving the
        # standard retry behavior in the UI.
        _LOGGER.warning("Could not load SomaFM station catalog during setup: %s", err)
        raise ConfigEntryNotReady(f"Could not load SomaFM station catalog: {err}") from err

    entry.runtime_data = client
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = client

    if not hass.data[DOMAIN].get("player_views_registered"):
        async_register_player_views(hass)
        hass.data[DOMAIN]["player_views_registered"] = True

    if not hass.data[DOMAIN].get("card_view_registered"):
        async_register_card_view(hass)
        hass.data[DOMAIN]["card_view_registered"] = True

    if not hass.data[DOMAIN].get("sidebar_panel_registered"):
        async_register_sidebar_panel(hass)
        hass.data[DOMAIN]["sidebar_panel_registered"] = True

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return True
