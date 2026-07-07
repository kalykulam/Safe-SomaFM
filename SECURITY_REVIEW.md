# Safe SomaFM security review notes

Safe SomaFM is intentionally small and auditable.

## Allowed behavior

- Loads the SomaFM station catalog from validated SomaFM endpoints.
- Loads SomaFM `.pls` playlists from validated SomaFM hosts.
- Resolves a selected station to a direct audio stream URL from the SomaFM playlist.
- Exposes Home Assistant's standard Media Source interface.
- Exposes authenticated local Home Assistant HTTP endpoints for the optional browser player:
  - `/safe_somafm/player`
  - `/api/safe_somafm/stations`
  - `/api/safe_somafm/resolve/{station_id}`

## Explicitly avoided behavior

- No credentials, tokens, cookies, or secrets.
- No local file reads or writes.
- No shell execution or subprocesses.
- No `eval`, `exec`, `pickle`, or dynamic imports.
- No third-party Python dependencies.
- No unauthenticated public endpoint.
- No generic URL proxy.
- No arbitrary user-supplied remote URL fetching.

## URL validation

The integration validates remote URLs before using them:

- station IDs must use a restricted ASCII character set;
- playlist URLs must point to `somafm.com` or a subdomain;
- playlist URLs must end with `.pls`;
- stream URLs must point to `somafm.com` or a subdomain;
- stream URLs must use `http` or `https`;
- URLs containing usernames or passwords are rejected;
- long URLs are rejected.

## Browser player model

The v0.3.3 browser player is not a generic proxy and does not accept arbitrary URLs. It only accepts a validated station ID, resolves that station through the Safe SomaFM client, and returns a direct SomaFM stream URL.

The browser, not Home Assistant, plays the audio. If the audio element reports an end/error/stall or stops advancing, the browser player asks Home Assistant for a fresh SomaFM stream URL and resumes playback.

## Residual risks

- This is still a custom Home Assistant integration. Installing custom code always adds trust risk.
- SomaFM controls the remote catalog and playlist contents. The integration validates host, scheme, size, and credentials, but it still depends on SomaFM availability and correctness.
- Browser autoplay policies may prevent automatic reconnection until the page has received a user interaction.
- Browser behavior may differ between Chrome, Firefox, Safari, mobile browsers, reverse proxies, and HTTPS setups.


## v0.3.3 note

The browser player was moved from `/safe_somafm/player` to `/safe_somafm/player` to avoid Home Assistant treating a direct browser visit as an unauthenticated API request. The player endpoints do not accept arbitrary URLs; they only expose the validated SomaFM station list and resolve validated SomaFM playlist entries.


## v0.3.4 stability and repository hygiene note

The recommended playback method is the local Safe SomaFM player at `/safe_somafm/player`.

The player remains limited to validated SomaFM station identifiers and SomaFM playlist/stream URLs. It is not intended to be a general-purpose proxy or arbitrary URL fetcher.

Repository hygiene:

- `__pycache__` folders are generated automatically by Python/Home Assistant.
- `.pyc` files are generated cache files.
- Neither should be committed to GitHub.
- The repository includes a `.gitignore` file to exclude them.


## v0.4.0 quality selection note

The quality selector does not allow arbitrary URLs. It only selects among validated SomaFM playlist URLs that were already present in the SomaFM station catalog.

The resolve endpoint accepts a quality identifier such as `auto`, `mp3_standard`, `mp3_highest`, `aac_highest`, `aacp_high`, or `aacp_low`. Unknown quality identifiers are rejected or fall back through the validated selection path; arbitrary URL input is never accepted.

`Auto (recommended)` preserves the stable v0.3.4 behavior by preferring the browser-friendly MP3 128 kbps playlist when available.


## v0.5.0 station metadata note

The player displays additional station metadata from the SomaFM catalog, including images, genre, listener counts, DJ names, and now-playing text when provided.

The displayed image URLs are still validated as SomaFM URLs. No arbitrary remote image or stream URL is accepted from user input.


## v0.6.0 visual interface note

The visual station grid uses metadata from the validated SomaFM catalog only. Station artwork URLs are still validated as SomaFM URLs before being exposed to the browser player.

The inline app icon/favicon is local SVG markup embedded in the player page. It does not fetch third-party icon assets and does not use official SomaFM or Home Assistant logos.

Dashboard embedding is intended through Home Assistant's Webpage/iframe card pointing to `/safe_somafm/player`.


## v0.6.1 brand assets note

Safe SomaFM ships original local brand images in `custom_components/safe_somafm/brand/`.

The images are static PNG files generated for this integration. They do not use official SomaFM or Home Assistant logos and do not contain executable content.


## v0.7.0 Lovelace card note

The Lovelace card is served locally from `/safe_somafm/card.js`.

It embeds the existing `/safe_somafm/player` page in an iframe and does not add a new playback backend. The card sanitizes the allowed iframe URL so it can only point to the Safe SomaFM local player path.

The card JavaScript is static integration code and does not fetch arbitrary third-party scripts.


## v0.8.4 sidebar and compact dashboard note

The compact dashboard mode is the same local player page with a restricted query parameter (`compact=1`) that only changes layout.

The sidebar panel registers a local Home Assistant panel and embeds `/safe_somafm/player`. It does not point to external URLs and does not add a second playback backend.


## v0.8.4 sidebar launcher note

The sidebar panel now acts as a local launcher for `/safe_somafm/player` and attempts to open it in a new tab.

The launcher URL is fixed to the local Safe SomaFM player path. It does not accept user-provided external URLs.


## v0.8.4 thumbnail sizing note

This version only adjusts CSS sizing for station thumbnails and card layout. It does not change data sources, network behavior, or playback logic.


## v0.8.4 compact layout note

This version only changes CSS and static text for the player layout. It does not change network behavior, accepted URLs, stream validation, or playback logic.


## v0.8.4 compact UI and README note

This version only adjusts visual layout and documentation:

- more compact dashboard station thumbnails;
- shorter player subtitle, keeping the version visible;
- rewritten GitHub README in English;
- added French README;
- documented that the sidebar launcher opens the full player in a new browser tab.

No playback logic or network validation behavior was changed.


## v0.8.4 station index visibility note

This release only adjusts page layout/CSS and compact-mode handling to keep the station grid visible. It does not change network validation, playback, reconnect behavior, or URL handling.


## v0.8.4 GitHub Pages index note

This version restores/adds a static `index.html` file for GitHub Pages. It is documentation only and is not used by the Home Assistant integration runtime.
