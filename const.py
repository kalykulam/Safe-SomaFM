"""Constants for the Safe SomaFM integration."""

DOMAIN = "safe_somafm"
NAME = "Safe SomaFM"
VERSION = "0.1.2"

SOMAFM_HOST = "somafm.com"
SOMAFM_BASE_URL = "https://somafm.com"
CHANNELS_URL = f"{SOMAFM_BASE_URL}/channels.xml"

USER_AGENT = "HomeAssistant-SafeSomaFM/0.1.2"

REQUEST_TIMEOUT_SECONDS = 10
MAX_XML_BYTES = 512 * 1024
MAX_PLAYLIST_BYTES = 64 * 1024
MAX_STATIONS = 500
MAX_STATION_ID_LENGTH = 64
MAX_URL_LENGTH = 2048

ALLOWED_STREAM_SCHEMES = {"http", "https"}
ALLOWED_PLAYLIST_SUFFIX = ".pls"
