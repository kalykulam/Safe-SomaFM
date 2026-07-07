"""Constants for the Safe SomaFM integration."""

DOMAIN = "safe_somafm"
NAME = "Safe SomaFM"
VERSION = "0.8.4"

SOMAFM_HOST = "somafm.com"
# JSON endpoints are preferred because they expose a structured playlists array.
# The XML endpoint is retained as a compatibility fallback for environments
# where one JSON endpoint is unavailable or blocked.
CHANNELS_JSON_URLS = (
    "https://somafm.com/channels.json",
    "https://api.somafm.com/channels.json",
)
CHANNELS_XML_URLS = (
    "https://somafm.com/channels.xml",
    "https://api.somafm.com/channels.xml",
)

USER_AGENT = "HomeAssistant-SafeSomaFM/0.4.0"

REQUEST_TIMEOUT_SECONDS = 10
STREAM_CONNECT_TIMEOUT_SECONDS = 10
STREAM_READ_TIMEOUT_SECONDS = 30
MAX_JSON_BYTES = 5 * 1024 * 1024
MAX_PLAYLIST_BYTES = 64 * 1024
MAX_STATIONS = 500
MAX_STATION_ID_LENGTH = 64
MAX_URL_LENGTH = 2048

ALLOWED_STREAM_SCHEMES = {"http", "https"}
ALLOWED_PLAYLIST_SUFFIX = ".pls"
PLAYLIST_CONTENT_TYPE = "audio/x-scpls"
# Keep the direct stream scheme exactly as SomaFM publishes it in the PLS file.
# Upgrading http streams to https looked safer, but local testing showed repeated
# browser playback stops around 6-8 minutes. This version tests whether the
# native SomaFM stream scheme is more stable in Home Assistant's browser player.
PRESERVE_STREAM_SCHEME = True
