"""Expose SomaFM as a Home Assistant media source."""

from __future__ import annotations

from homeassistant.components.media_player import BrowseError, MediaClass, MediaType
from homeassistant.components.media_source import (
    BrowseMediaSource,
    MediaSource,
    MediaSourceItem,
    PlayMedia,
    Unresolvable,
    generate_media_source_id,
)
from homeassistant.core import HomeAssistant

from .somafm import SafeSomaFMClient, SomaFMError, SomaFMValidationError
from .const import DOMAIN, NAME


async def async_get_media_source(hass: HomeAssistant) -> SafeSomaFMMediaSource:
    """Set up the Safe SomaFM media source."""
    return SafeSomaFMMediaSource(hass)


class SafeSomaFMMediaSource(MediaSource):
    """Provide SomaFM stations as a browsable media source."""

    name = NAME

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the media source."""
        super().__init__(DOMAIN)
        self.hass = hass

    @property
    def client(self) -> SafeSomaFMClient:
        """Return the configured client."""
        entries = self.hass.config_entries.async_entries(DOMAIN)
        if not entries:
            raise BrowseError("Safe SomaFM is not configured")
        return entries[0].runtime_data

    async def async_resolve_media(self, item: MediaSourceItem) -> PlayMedia:
        """Resolve a SomaFM station to a playable stream URL."""
        station_id = item.identifier.strip("/")
        try:
            stream_url = await self.client.async_resolve_station(station_id)
        except SomaFMValidationError as err:
            raise Unresolvable(
                translation_domain=DOMAIN,
                translation_key="station_not_found",
            ) from err
        except SomaFMError as err:
            raise Unresolvable(
                translation_domain=DOMAIN,
                translation_key="station_unavailable",
            ) from err

        return PlayMedia(stream_url, "audio/mpeg")

    async def async_browse_media(self, item: MediaSourceItem) -> BrowseMediaSource:
        """Browse the SomaFM station catalog."""
        if item.identifier:
            raise BrowseError("Safe SomaFM only supports browsing the root catalog")

        try:
            stations = await self.client.async_get_stations()
        except SomaFMError as err:
            raise BrowseError("Could not load SomaFM stations") from err

        children = [
            BrowseMediaSource(
                domain=DOMAIN,
                identifier=station.station_id,
                media_class=MediaClass.MUSIC,
                media_content_type=MediaType.MUSIC,
                title=station.title,
                can_play=True,
                can_expand=False,
                thumbnail=station.image_url,
            )
            for station in stations.values()
        ]

        return BrowseMediaSource(
            domain=DOMAIN,
            identifier=None,
            media_class=MediaClass.DIRECTORY,
            media_content_type=MediaType.MUSIC,
            title=NAME,
            can_play=False,
            can_expand=True,
            children=children,
        )
