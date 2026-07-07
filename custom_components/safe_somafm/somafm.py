"""Small, defensive SomaFM client for Home Assistant."""

from __future__ import annotations

import asyncio
import json
import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from random import SystemRandom
from time import monotonic
from typing import Any, Final
from urllib.parse import urlparse

from aiohttp import ClientError, ClientResponseError, ClientSession, ClientTimeout
from aiohttp.web import StreamResponse

from .const import (
    ALLOWED_PLAYLIST_SUFFIX,
    ALLOWED_STREAM_SCHEMES,
    CHANNELS_JSON_URLS,
    CHANNELS_XML_URLS,
    MAX_JSON_BYTES,
    MAX_PLAYLIST_BYTES,
    MAX_STATION_ID_LENGTH,
    MAX_STATIONS,
    MAX_URL_LENGTH,
    PRESERVE_STREAM_SCHEME,
    REQUEST_TIMEOUT_SECONDS,
    SOMAFM_HOST,
    STREAM_CONNECT_TIMEOUT_SECONDS,
    STREAM_READ_TIMEOUT_SECONDS,
    USER_AGENT,
)

_LOGGER = logging.getLogger(__name__)
_RANDOM = SystemRandom()

_CACHE_TTL_SECONDS: Final = 60 * 60
_SAFE_STATION_ID_CHARS: Final = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
)

QUALITY_AUTO: Final = "auto"
QUALITY_MP3_STANDARD: Final = "mp3_standard"
QUALITY_MP3_HIGHEST: Final = "mp3_highest"
QUALITY_AAC_HIGHEST: Final = "aac_highest"
QUALITY_AACP_HIGH: Final = "aacp_high"
QUALITY_AACP_LOW: Final = "aacp_low"

QUALITY_LABELS: Final[dict[str, str]] = {
    QUALITY_AUTO: "Auto (recommended)",
    QUALITY_MP3_STANDARD: "MP3 128 kbps (recommended)",
    QUALITY_MP3_HIGHEST: "MP3 highest",
    QUALITY_AAC_HIGHEST: "AAC highest",
    QUALITY_AACP_HIGH: "AAC+ high",
    QUALITY_AACP_LOW: "AAC+ low bandwidth",
}

# Auto keeps the v0.3.4 behavior that was stable in local testing.
_PLAYLIST_PREFERENCE: Final = (
    ("mp3", "standard", QUALITY_MP3_STANDARD),
    ("mp3", "highest", QUALITY_MP3_HIGHEST),
    ("aac", "highest", QUALITY_AAC_HIGHEST),
    ("aacp", "high", QUALITY_AACP_HIGH),
    ("aacp", "low", QUALITY_AACP_LOW),
)
_CONTENT_TYPES: Final = {
    "mp3": "audio/mpeg",
    "aac": "audio/aac",
    "aacp": "audio/aacp",
}
_XML_PLAYLIST_FIELDS: Final = (
    ("pls", "mp3", "standard", QUALITY_MP3_STANDARD),
    ("highestpls", "mp3", "highest", QUALITY_MP3_HIGHEST),
    ("fastpls", "aac", "highest", QUALITY_AAC_HIGHEST),
    ("slowpls", "aacp", "low", QUALITY_AACP_LOW),
)
_XML_IMAGE_FIELDS: Final = ("xlimage", "largeimage", "image")


class SomaFMError(Exception):
    """Base error for SomaFM integration failures."""


class SomaFMValidationError(SomaFMError):
    """Raised when remote data does not pass defensive validation."""


@dataclass(frozen=True, slots=True)
class StreamOption:
    """A supported SomaFM playlist variant for one station."""

    quality_id: str
    label: str
    playlist_url: str
    content_type: str
    stream_format: str
    stream_quality: str


@dataclass(frozen=True, slots=True)
class Station:
    """A single SomaFM station."""

    station_id: str
    title: str
    description: str
    playlist_url: str
    content_type: str
    image_url: str | None = None
    large_image_url: str | None = None
    genre: str = ""
    dj: str = ""
    listeners: int | None = None
    last_playing: str = ""
    stream_options: tuple[StreamOption, ...] = ()


@dataclass(frozen=True, slots=True)
class ResolvedStream:
    """A playable stream URL and its best-known content type."""

    url: str
    content_type: str
    quality_id: str
    quality_label: str


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
    if parsed.scheme not in {"http", "https"}:
        raise SomaFMValidationError("Remote URL has an unsupported scheme")
    if not _is_somafm_host(parsed.hostname):
        raise SomaFMValidationError("Remote URL host is not somafm.com")
    if parsed.username or parsed.password:
        raise SomaFMValidationError("Remote URL must not contain credentials")
    if playlist and not parsed.path.endswith(ALLOWED_PLAYLIST_SUFFIX):
        raise SomaFMValidationError("Playlist URL does not end in .pls")
    if parsed.scheme == "http":
        return parsed._replace(scheme="https").geturl()
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
    if parsed.scheme == "http" and not PRESERVE_STREAM_SCHEME:
        return parsed._replace(scheme="https").geturl()
    return url


def _text(value: Any, *, max_length: int) -> str:
    if value is None:
        return ""
    return str(value).strip()[:max_length]


def _looks_like_standard_mp3_playlist(url: str) -> bool:
    """Return true for station.pls style 128 kbps MP3 playlists."""
    parsed = urlparse(url)
    filename = parsed.path.rsplit("/", 1)[-1].lower()
    if not filename.endswith(".pls"):
        return False
    stem = filename[:-4]
    return not any(char.isdigit() for char in stem)


def _quality_id_for(stream_format: str, stream_quality: str) -> str | None:
    for wanted_format, wanted_quality, quality_id in _PLAYLIST_PREFERENCE:
        if stream_format == wanted_format and stream_quality == wanted_quality:
            return quality_id
    return None


def _sort_options(options: list[StreamOption]) -> tuple[StreamOption, ...]:
    order = {quality_id: index for index, (_, _, quality_id) in enumerate(_PLAYLIST_PREFERENCE)}
    deduped: dict[str, StreamOption] = {}
    for option in options:
        deduped.setdefault(option.quality_id, option)
    return tuple(sorted(deduped.values(), key=lambda item: order.get(item.quality_id, 999)))


def _select_default_option(options: tuple[StreamOption, ...]) -> StreamOption:
    for _, _, quality_id in _PLAYLIST_PREFERENCE:
        for option in options:
            if option.quality_id == quality_id:
                return option
    if options:
        return options[0]
    raise SomaFMValidationError("No supported SomaFM playlist URL found for station")


def _json_stream_options(playlists: Any) -> tuple[StreamOption, ...]:
    if not isinstance(playlists, list):
        raise SomaFMValidationError("Station playlist data is not a list")

    normalized: list[StreamOption] = []
    for item in playlists:
        if not isinstance(item, dict):
            continue
        playlist_url = item.get("url")
        stream_format = _text(item.get("format"), max_length=16).lower()
        stream_quality = _text(item.get("quality"), max_length=16).lower()
        if not isinstance(playlist_url, str):
            continue
        if stream_format not in _CONTENT_TYPES:
            continue
        try:
            validated_url = _validate_https_somafm_url(playlist_url, playlist=True)
        except SomaFMValidationError:
            continue
        normalized_quality = stream_quality
        if stream_format == "mp3" and _looks_like_standard_mp3_playlist(validated_url):
            normalized_quality = "standard"

        quality_id = _quality_id_for(stream_format, normalized_quality)
        if quality_id is None:
            continue
        normalized.append(
            StreamOption(
                quality_id=quality_id,
                label=QUALITY_LABELS[quality_id],
                playlist_url=validated_url,
                content_type=_CONTENT_TYPES[stream_format],
                stream_format=stream_format,
                stream_quality=normalized_quality,
            )
        )

    options = _sort_options(normalized)
    if not options:
        raise SomaFMValidationError("No supported SomaFM playlist URL found for station")
    return options


def _parse_json_stations(data: Any) -> dict[str, Station]:
    if isinstance(data, dict):
        channels = data.get("channels")
    else:
        channels = data

    if not isinstance(channels, list):
        raise SomaFMValidationError("SomaFM JSON catalog does not contain a channel list")

    stations: dict[str, Station] = {}
    skipped = 0
    for channel in channels:
        if len(stations) >= MAX_STATIONS:
            break
        if not isinstance(channel, dict):
            skipped += 1
            continue

        station_id = _text(channel.get("id"), max_length=MAX_STATION_ID_LENGTH)
        if not _is_safe_station_id(station_id):
            skipped += 1
            continue

        try:
            options = _json_stream_options(channel.get("playlists"))
            default_option = _select_default_option(options)
            image_url = _text(channel.get("image"), max_length=MAX_URL_LENGTH) or None
            if image_url:
                image_url = _validate_https_somafm_url(image_url)

            large_image_url = (
                _text(channel.get("largeimage"), max_length=MAX_URL_LENGTH)
                or _text(channel.get("xlimage"), max_length=MAX_URL_LENGTH)
                or image_url
            )
            if large_image_url:
                large_image_url = _validate_https_somafm_url(large_image_url)
        except SomaFMValidationError:
            skipped += 1
            continue

        stations[station_id] = Station(
            station_id=station_id,
            title=_text(channel.get("title"), max_length=160) or station_id,
            description=_text(channel.get("description"), max_length=500),
            playlist_url=default_option.playlist_url,
            content_type=default_option.content_type,
            image_url=image_url,
            large_image_url=large_image_url,
            genre=_text(channel.get("genre"), max_length=120),
            dj=_text(channel.get("dj"), max_length=120),
            listeners=_int_or_none(channel.get("listeners")),
            last_playing=(
                _text(channel.get("lastPlaying"), max_length=240)
                or _text(channel.get("lastplaying"), max_length=240)
            ),
            stream_options=options,
        )

    if not stations:
        raise SomaFMValidationError(
            f"No valid SomaFM stations found in JSON catalog; checked {len(channels)} entries, skipped {skipped}"
        )

    return dict(sorted(stations.items(), key=lambda item: item[1].title.casefold()))




def _int_or_none(value: Any) -> int | None:
    """Return a small non-negative integer from remote metadata, when possible."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if 0 <= value <= 10_000_000 else None
    if isinstance(value, str):
        cleaned = value.strip().replace(",", "")
        if cleaned.isdecimal():
            number = int(cleaned)
            return number if 0 <= number <= 10_000_000 else None
    return None


def _child_text(element: ET.Element, tag: str, *, max_length: int) -> str:
    child = element.find(tag)
    if child is None or child.text is None:
        return ""
    return child.text.strip()[:max_length]


def _xml_stream_options(channel: ET.Element) -> tuple[StreamOption, ...]:
    options: list[StreamOption] = []
    for tag, stream_format, stream_quality, quality_id in _XML_PLAYLIST_FIELDS:
        playlist_url = _child_text(channel, tag, max_length=MAX_URL_LENGTH)
        if not playlist_url:
            continue
        try:
            validated = _validate_https_somafm_url(playlist_url, playlist=True)
        except SomaFMValidationError:
            continue
        options.append(
            StreamOption(
                quality_id=quality_id,
                label=QUALITY_LABELS[quality_id],
                playlist_url=validated,
                content_type=_CONTENT_TYPES[stream_format],
                stream_format=stream_format,
                stream_quality=stream_quality,
            )
        )
    sorted_options = _sort_options(options)
    if not sorted_options:
        raise SomaFMValidationError("No supported XML playlist URL found for station")
    return sorted_options


def _parse_xml_stations(xml_bytes: bytes) -> dict[str, Station]:
    lower_prefix = xml_bytes[:2048].lower()
    if b"<!doctype" in lower_prefix or b"<!entity" in lower_prefix:
        raise SomaFMValidationError("Unsafe XML declaration rejected")

    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as err:
        raise SomaFMValidationError("Could not parse SomaFM XML catalog") from err

    channels = list(root.findall(".//channel"))
    if not channels:
        raise SomaFMValidationError("SomaFM XML catalog does not contain channels")

    stations: dict[str, Station] = {}
    skipped = 0
    for channel in channels:
        if len(stations) >= MAX_STATIONS:
            break

        station_id = _text(channel.get("id"), max_length=MAX_STATION_ID_LENGTH)
        if not station_id:
            station_id = _child_text(channel, "id", max_length=MAX_STATION_ID_LENGTH)
        if not _is_safe_station_id(station_id):
            skipped += 1
            continue

        try:
            options = _xml_stream_options(channel)
            default_option = _select_default_option(options)
            image_url = None
            large_image_url = None
            for image_tag in _XML_IMAGE_FIELDS:
                candidate = _child_text(channel, image_tag, max_length=MAX_URL_LENGTH)
                if not candidate:
                    continue
                try:
                    validated_image = _validate_https_somafm_url(candidate)
                    if image_url is None:
                        image_url = validated_image
                    if image_tag in {"xlimage", "largeimage"} and large_image_url is None:
                        large_image_url = validated_image
                except SomaFMValidationError:
                    continue
            if large_image_url is None:
                large_image_url = image_url
        except SomaFMValidationError:
            skipped += 1
            continue

        listeners_text = _child_text(channel, "listeners", max_length=32)

        stations[station_id] = Station(
            station_id=station_id,
            title=_child_text(channel, "title", max_length=160) or station_id,
            description=_child_text(channel, "description", max_length=500),
            playlist_url=default_option.playlist_url,
            content_type=default_option.content_type,
            image_url=image_url,
            large_image_url=large_image_url,
            genre=_child_text(channel, "genre", max_length=120),
            dj=_child_text(channel, "dj", max_length=120),
            listeners=_int_or_none(listeners_text),
            last_playing=(
                _child_text(channel, "lastPlaying", max_length=240)
                or _child_text(channel, "lastplaying", max_length=240)
            ),
            stream_options=options,
        )

    if not stations:
        raise SomaFMValidationError(
            f"No valid SomaFM stations found in XML catalog; checked {len(channels)} entries, skipped {skipped}"
        )

    return dict(sorted(stations.items(), key=lambda item: item[1].title.casefold()))


def _parse_playlist_urls(playlist_text: str) -> list[str]:
    stream_urls: list[str] = []
    for raw_line in playlist_text.splitlines():
        line = raw_line.strip()
        if not line or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key.lower().startswith("file"):
            try:
                stream_url = _validate_stream_url(value.strip())
            except SomaFMValidationError:
                continue
            if stream_url not in stream_urls:
                stream_urls.append(stream_url)

    if not stream_urls:
        raise SomaFMValidationError("Playlist contained no valid stream URL")

    _RANDOM.shuffle(stream_urls)
    return stream_urls


def _select_station_option(station: Station, quality_id: str | None) -> StreamOption:
    if quality_id and quality_id != QUALITY_AUTO:
        for option in station.stream_options:
            if option.quality_id == quality_id:
                return option
        raise SomaFMValidationError("Requested quality is not available for this station")
    return _select_default_option(station.stream_options)


class SafeSomaFMClient:
    """Fetch and validate SomaFM catalog and playlists."""

    def __init__(self, session: ClientSession) -> None:
        self._session = session
        self._stations: dict[str, Station] | None = None
        self._stations_loaded_at = 0.0

    async def _get_bytes(self, url: str, *, max_bytes: int, accept: str) -> bytes:
        timeout = ClientTimeout(total=REQUEST_TIMEOUT_SECONDS)
        headers = {"User-Agent": USER_AGENT, "Accept": accept}
        try:
            async with self._session.get(url, headers=headers, timeout=timeout) as response:
                response.raise_for_status()
                content_length = response.content_length
                if content_length is not None and content_length > max_bytes:
                    raise SomaFMValidationError(
                        f"Remote response is too large: content_length={content_length}"
                    )

                if content_length is not None:
                    body = await response.read()
                    if len(body) > max_bytes:
                        raise SomaFMValidationError("Remote response exceeded size limit")
                    return body

                chunks: list[bytes] = []
                total = 0
                async for chunk in response.content.iter_chunked(64 * 1024):
                    total += len(chunk)
                    if total > max_bytes:
                        raise SomaFMValidationError("Remote response exceeded size limit")
                    chunks.append(chunk)
                return b"".join(chunks)
        except asyncio.TimeoutError as err:
            raise SomaFMError(f"Timed out while fetching {url}") from err
        except ClientResponseError as err:
            raise SomaFMError(f"HTTP {err.status} while fetching {url}") from err
        except ClientError as err:
            raise SomaFMError(f"Network error while fetching {url}: {err!r}") from err

    async def _load_json_catalog(self) -> dict[str, Station]:
        last_error: Exception | None = None
        for catalog_url in CHANNELS_JSON_URLS:
            try:
                json_bytes = await self._get_bytes(
                    catalog_url,
                    max_bytes=MAX_JSON_BYTES,
                    accept="application/json,text/json,*/*",
                )
                json_text = json_bytes.decode("utf-8", errors="replace")
                data = await asyncio.to_thread(json.loads, json_text, strict=False)
                return _parse_json_stations(data)
            except Exception as err:  # noqa: BLE001 - try fallback endpoint, then report cleanly.
                last_error = err
                _LOGGER.warning("Could not load SomaFM JSON catalog from %s: %s", catalog_url, err)

        raise SomaFMError("Could not load SomaFM JSON catalog from any endpoint") from last_error

    async def _load_xml_catalog(self) -> dict[str, Station]:
        last_error: Exception | None = None
        for catalog_url in CHANNELS_XML_URLS:
            try:
                xml_bytes = await self._get_bytes(
                    catalog_url,
                    max_bytes=MAX_JSON_BYTES,
                    accept="application/xml,text/xml,*/*",
                )
                return await asyncio.to_thread(_parse_xml_stations, xml_bytes)
            except Exception as err:  # noqa: BLE001 - try fallback endpoint, then report cleanly.
                last_error = err
                _LOGGER.warning("Could not load SomaFM XML catalog from %s: %s", catalog_url, err)

        raise SomaFMError("Could not load SomaFM XML catalog from any endpoint") from last_error

    async def async_get_stations(self, *, force_refresh: bool = False) -> dict[str, Station]:
        """Return validated stations, refreshed periodically in memory only."""
        now = monotonic()
        if (
            not force_refresh
            and self._stations is not None
            and now - self._stations_loaded_at < _CACHE_TTL_SECONDS
        ):
            return self._stations

        json_error: Exception | None = None
        try:
            self._stations = await self._load_json_catalog()
        except Exception as err:  # noqa: BLE001 - XML fallback keeps the integration usable.
            json_error = err
            _LOGGER.warning("SomaFM JSON catalog failed, trying XML fallback: %s", err)
            try:
                self._stations = await self._load_xml_catalog()
            except Exception as xml_error:  # noqa: BLE001 - keep setup error concise, logs have details.
                raise SomaFMError(
                    "Could not load SomaFM station catalog from JSON or XML endpoints"
                ) from xml_error or json_error

        self._stations_loaded_at = now
        return self._stations

    async def _get_station(self, station_id: str) -> Station:
        if not _is_safe_station_id(station_id):
            raise SomaFMValidationError("Unsafe station id")

        stations = await self.async_get_stations()
        station = stations.get(station_id)
        if station is None:
            raise SomaFMValidationError("Unknown station id")
        return station

    async def async_get_station_content_type(self, station_id: str) -> str:
        """Return the default content type for a station."""
        station = await self._get_station(station_id)
        return station.content_type

    async def async_get_station_stream_urls(
        self, station_id: str, quality_id: str | None = QUALITY_AUTO
    ) -> list[str]:
        """Resolve a station PLS playlist to validated direct stream URLs."""
        station = await self._get_station(station_id)
        option = _select_station_option(station, quality_id)
        playlist_bytes = await self._get_bytes(
            option.playlist_url,
            max_bytes=MAX_PLAYLIST_BYTES,
            accept="audio/x-scpls,text/plain,*/*",
        )
        playlist_text = playlist_bytes.decode("utf-8", errors="replace")
        return _parse_playlist_urls(playlist_text)

    async def async_resolve_station(
        self, station_id: str, quality_id: str | None = QUALITY_AUTO
    ) -> ResolvedStream:
        """Resolve a station id to a browser-playable direct audio stream URL."""
        station = await self._get_station(station_id)
        option = _select_station_option(station, quality_id)
        stream_urls = await self.async_get_station_stream_urls(station_id, option.quality_id)
        selected_url = _RANDOM.choice(stream_urls)
        parsed = urlparse(selected_url)
        _LOGGER.warning(
            "Resolved SomaFM station %s using playlist %s quality=%s to %s stream host=%s path=%s content_type=%s",
            station_id,
            option.playlist_url,
            option.quality_id,
            parsed.scheme,
            parsed.hostname,
            parsed.path,
            option.content_type,
        )
        return ResolvedStream(
            url=selected_url,
            content_type=option.content_type,
            quality_id=option.quality_id,
            quality_label=option.label,
        )

    async def async_relay_station(self, station_id: str, response: StreamResponse) -> None:
        """Relay a station stream for diagnostics only."""
        station = await self._get_station(station_id)
        stream_urls = await self.async_get_station_stream_urls(station_id)
        if not stream_urls:
            raise SomaFMError("No stream URL available")

        timeout = ClientTimeout(
            total=None,
            sock_connect=STREAM_CONNECT_TIMEOUT_SECONDS,
            sock_read=STREAM_READ_TIMEOUT_SECONDS,
        )
        headers = {
            "User-Agent": USER_AGENT,
            "Accept": station.content_type + ",audio/*,*/*",
            "Icy-MetaData": "0",
        }

        async with self._session.get(stream_urls[0], headers=headers, timeout=timeout) as upstream:
            upstream.raise_for_status()
            async for chunk in upstream.content.iter_chunked(16 * 1024):
                if chunk:
                    await response.write(chunk)
