# Safe SomaFM for Home Assistant

Safe SomaFM is a defensive Home Assistant custom integration for listening to [SomaFM](https://somafm.com/) streams from Home Assistant.

It provides:

- a local Home Assistant browser player;
- a compact Lovelace dashboard card;
- a sidebar launcher that opens the full player in a new browser tab;
- station artwork, descriptions, genre, listeners, DJ and now-playing metadata when SomaFM provides it;
- selectable stream quality / bitrate;
- automatic reconnect logic for long listening sessions.

Current version: **v0.8.3**

French documentation: [README.fr.md](README.fr.md)

---

## Why this integration exists

The standard Home Assistant Media Browser can hand the stream directly to the browser. In testing, some browsers stopped long-running SomaFM streams after several minutes.

Safe SomaFM uses a local Home Assistant player page with automatic reconnect handling. The full player has been tested successfully for long listening sessions.

---

## Features

### Local player

Open the full player directly:

```text
/safe_somafm/player
```

The full player shows:

- station artwork;
- a searchable station grid;
- station metadata;
- quality / bitrate selection;
- play and stop controls;
- automatic reconnect status.

### Compact dashboard mode

The Lovelace card uses the compact player mode:

```text
/safe_somafm/player?compact=1
```

This mode is designed for dashboard columns and uses smaller station thumbnails.

### Sidebar launcher

The integration registers a **Safe SomaFM** item in the Home Assistant left sidebar.

Clicking the sidebar item attempts to open the full player in a **new browser tab**.

If the browser blocks the automatic new tab, a small fallback page is shown with an **Open Safe SomaFM** button.

### Lovelace card

The integration serves a local card resource:

```text
/safe_somafm/card.js
```

Add it as a Home Assistant dashboard resource:

```text
JavaScript module
```

Then add a card:

```yaml
type: custom:safe-somafm-card
title: Safe SomaFM
height: 320px
```

Optional larger version:

```yaml
type: custom:safe-somafm-card
title: Safe SomaFM
height: 420px
show_header: true
```

---

## Installation

### Manual installation

1. Copy this folder:

```text
custom_components/safe_somafm/
```

to your Home Assistant configuration directory:

```text
/config/custom_components/safe_somafm/
```

2. Restart Home Assistant completely.
3. Go to **Settings → Devices & services → Add integration**.
4. Search for **Safe SomaFM**.
5. Add the integration.

### Updating

When updating manually:

1. Stop or restart Home Assistant.
2. Delete the old folder:

```text
/config/custom_components/safe_somafm/
```

3. Copy the new `safe_somafm` folder.
4. Restart Home Assistant.
5. Refresh the browser with `Ctrl + F5`.

---

## Dashboard setup

### Add the card resource

In Home Assistant:

1. Open a dashboard.
2. Click **Edit dashboard**.
3. Open the top-right menu.
4. Go to **Resources**.
5. Add:

```text
/safe_somafm/card.js
```

Resource type:

```text
JavaScript module
```

### Add the card

```yaml
type: custom:safe-somafm-card
title: Safe SomaFM
height: 320px
```

---

## Security posture

Safe SomaFM is intentionally limited:

- no user credentials;
- no secrets;
- no external Python dependencies;
- no shell execution;
- no dynamic imports;
- no arbitrary proxy;
- no arbitrary stream URL input;
- station IDs are validated;
- playlist and image URLs are validated as SomaFM URLs;
- playback endpoints are local Home Assistant endpoints.

The sidebar launcher only opens:

```text
/safe_somafm/player
```

It does not accept external URLs.

More details are available in [SECURITY_REVIEW.md](SECURITY_REVIEW.md).

---

## Files

```text
custom_components/safe_somafm/
├── __init__.py
├── card.py
├── config_flow.py
├── const.py
├── manifest.json
├── media_source.py
├── panel.py
├── player.py
├── somafm.py
├── strings.json
└── brand/
```

---

## Notes

Safe SomaFM is not affiliated with SomaFM or Home Assistant.

SomaFM names, station names and station artwork belong to SomaFM. The Safe SomaFM integration icon is original and does not use official SomaFM or Home Assistant logos.
