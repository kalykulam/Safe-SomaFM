"""Safe SomaFM integration for Home Assistant.

Security posture:
- no user credentials
- no dynamic imports
- no shell execution
- no local file reads/writes
- no inbound HTTP endpoint
- outbound HTTPS only to somafm.com for the station catalog and playlists
"""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .somafm import SafeSomaFMClient, SomaFMError
from .const import DOMAIN



async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Safe SomaFM from a config entry."""
    session = async_get_clientsession(hass)
    client = SafeSomaFMClient(session)

    try:
        await client.async_get_stations(force_refresh=True)
    except SomaFMError as err:
        raise ConfigEntryNotReady("Could not load SomaFM station catalog") from err

    entry.runtime_data = client
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = client
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return True
