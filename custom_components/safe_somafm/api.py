"""Small, defensive SomaFM client for Home Assistant."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from time import monotonic
from typing import Final
from urllib.parse import urlparse
from xml.etree import ElementTree as ET

from aiohttp import ClientError, ClientResponseError, ClientSession, ClientTimeout

from .const import (
    ALLOWED_PLAYLIST_SUFFIX,
    ALLOWED_STREAM_SCHEMES,
    CHANNELS_URL,
    MAX_PLAYLIST_BYTES,
    MAX_STATION_ID_LENGTH,
    MAX_STATIONS,
    MAX_URL_LENGTH,
    MAX_XML_BYTES,
    REQUEST_TIMEOUT_SECONDS,
    SOMAFM_HOST,
    USER_AGENT,
)

_CACHE_TTL_SECONDS: Final = 60 * 60
_SAFE_STATION_ID_CHARS: Final = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
)

# SomaFM's channels.xml usually exposes several playlist tags, for example:
# <highestpls format="aac">...</highestpls>, <fastpls format="mp3">...</fastpls>.
# We prefer stable PLS links, with AAC first, while keeping a small fallback set.
_PLAYLIST_TAG_PRIORITY: Final = (
    ("highestpls", "aac"),
    ("highestpls", "mp3"),
    ("fastpls", "aac"),
    ("fastpls", "mp3"),
    ("fastpls", "aacp"),
    ("slowpls", "aacp"),
    ("pls", None),
)


class SomaFMError(Exception):
    """Base error for SomaFM integration failures."""


class SomaFMValidationError(SomaFMError):
    """Raised when remote data does not pass defensive validation."""


@dataclass(frozen=True, slots=True)
class Station:
    """A single SomaFM station."""

    station_id: str
    title: str
    description: str
    playlist_url: str
    image_url: str | None = None


def _is_safe_station_id(station_id: str) -> bool:
    return (
        1 <= len(station_id) <= MAX_STATION_ID_LENGTH
        and all(ch in _SAFE_STATION_ID_CHARS for ch in station_id)
    )


def _is_somafm_host(hostname: str | None) -> bool:
    if hostname is None:
        return False
    hostname = hostname.lower().rstrip(".")
    return hostname == SOMAFM_HOST or hostname.endswith(f".{SOMAFM_HOST}")


def _validate_https_somafm_url(url: str, *, playlist: bool = False) -> str:
    url = url.strip()
    if len(url) > MAX_URL_LENGTH:
        raise SomaFMValidationError("Remote URL is too long")

    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise SomaFMValidationError("Remote catalog URL is not HTTPS")
    if not _is_somafm_host(parsed.hostname):
        raise SomaFMValidationError("Remote catalog URL host is not somafm.com")
    if parsed.username or parsed.password:
        raise SomaFMValidationError("Remote URL must not contain credentials")
    if playlist and not parsed.path.endswith(ALLOWED_PLAYLIST_SUFFIX):
        raise SomaFMValidationError("Playlist URL does not end in .pls")
    return url


def _validate_stream_url(url: str) -> str:
    url = url.strip()
    if len(url) > MAX_URL_LENGTH:
        raise SomaFMValidationError("Stream URL is too long")

    parsed = urlparse(url)
    if parsed.scheme not in ALLOWED_STREAM_SCHEMES:
        raise SomaFMValidationError("Stream URL has an unsupported scheme")
    if not _is_somafm_host(parsed.hostname):
        raise SomaFMValidationError("Stream URL host is not somafm.com")
    if parsed.username or parsed.password:
        raise SomaFMValidationError("Stream URL must not contain credentials")
    return url


def _text_or_empty(element: ET.Element, tag: str) -> str:
    found = element.find(tag)
    if found is None or found.text is None:
        return ""
    return found.text.strip()


def _find_playlist_url(channel: ET.Element) -> str:
    for tag_name, wanted_format in _PLAYLIST_TAG_PRIORITY:
        for candidate in channel.findall(tag_name):
            if wanted_format is not None:
                actual_format = (candidate.get("format") or "").strip().lower()
                if actual_format != wanted_format:
                    continue
            if candidate.text and candidate.text.strip():
                return _validate_https_somafm_url(candidate.text, playlist=True)
    raise SomaFMValidationError("No supported SomaFM playlist URL found for station")


def _parse_stations(xml_bytes: bytes) -> dict[str, Station]:
    # xml.etree does not fetch external entities, but rejecting declarations keeps
    # parser behavior simple and limits entity-expansion style attacks.
    prefix = xml_bytes[:512].lower()
    if b"<!doctype" in prefix or b"<!entity" in prefix:
        raise SomaFMValidationError("XML declarations containing entities are not allowed")

    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as err:
        raise SomaFMValidationError("Could not parse SomaFM station XML") from err

    channels = root.findall("channel")
    if not channels:
        channels = root.findall("./channels/channel")

    stations: dict[str, Station] = {}
    skipped = 0
    for channel in channels:
        if len(stations) >= MAX_STATIONS:
            break

        station_id = (channel.get("id") or "").strip()
        if not _is_safe_station_id(station_id):
            skipped += 1
            continue

        title = _text_or_empty(channel, "title") or station_id
        description = _text_or_empty(channel, "description")
        image_url = _text_or_empty(channel, "image") or None

        try:
            playlist_url = _find_playlist_url(channel)
            if image_url:
                image_url = _validate_https_somafm_url(image_url)
        except SomaFMValidationError:
            skipped += 1
            continue

        stations[station_id] = Station(
            station_id=station_id,
            title=title[:160],
            description=description[:500],
            playlist_url=playlist_url,
            image_url=image_url,
        )

    if not stations:
        raise SomaFMValidationError(
            f"No valid SomaFM stations found; checked {len(channels)} channel elements, skipped {skipped}"
        )

    return dict(sorted(stations.items(), key=lambda item: item[1].title.casefold()))


def _parse_playlist(playlist_text: str) -> str:
    for raw_line in playlist_text.splitlines():
        line = raw_line.strip()
        if not line or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key.lower().startswith("file"):
            return _validate_stream_url(value.strip())
    raise SomaFMValidationError("Playlist contained no valid stream URL")


class SafeSomaFMClient:
    """Fetch and validate SomaFM catalog and playlists."""

    def __init__(self, session: ClientSession) -> None:
        self._session = session
        self._stations: dict[str, Station] | None = None
        self._stations_loaded_at = 0.0

    async def _get_bytes(self, url: str, *, max_bytes: int) -> bytes:
        timeout = ClientTimeout(total=REQUEST_TIMEOUT_SECONDS)
        headers = {"User-Agent": USER_AGENT, "Accept": "application/xml,text/plain,*/*"}
        try:
            async with self._session.get(url, headers=headers, timeout=timeout) as response:
                response.raise_for_status()
                content_length = response.content_length
                if content_length is not None and content_length > max_bytes:
                    raise SomaFMValidationError("Remote response is too large")

                body = await response.content.read(max_bytes + 1)
                if len(body) > max_bytes:
                    raise SomaFMValidationError("Remote response exceeded size limit")
                return body
        except asyncio.TimeoutError as err:
            raise SomaFMError("Timed out while fetching SomaFM data") from err
        except (ClientError, ClientResponseError) as err:
            raise SomaFMError("Could not fetch SomaFM data") from err

    async def async_get_stations(self, *, force_refresh: bool = False) -> dict[str, Station]:
        """Return validated stations, refreshed periodically in memory only."""
        now = monotonic()
        if (
            not force_refresh
            and self._stations is not None
            and now - self._stations_loaded_at < _CACHE_TTL_SECONDS
        ):
            return self._stations

        xml_bytes = await self._get_bytes(CHANNELS_URL, max_bytes=MAX_XML_BYTES)
        self._stations = _parse_stations(xml_bytes)
        self._stations_loaded_at = now
        return self._stations

    async def async_resolve_station(self, station_id: str) -> str:
        """Resolve a station id to a validated playable stream URL."""
        if not _is_safe_station_id(station_id):
            raise SomaFMValidationError("Unsafe station id")

        stations = await self.async_get_stations()
        station = stations.get(station_id)
        if station is None:
            raise SomaFMValidationError("Unknown station id")

        playlist_bytes = await self._get_bytes(station.playlist_url, max_bytes=MAX_PLAYLIST_BYTES)
        playlist_text = playlist_bytes.decode("utf-8", errors="replace")
        return _parse_playlist(playlist_text)
