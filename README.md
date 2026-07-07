# Safe SomaFM for Home Assistant

Safe SomaFM is a defensive Home Assistant custom integration for listening to [SomaFM](https://somafm.com/) streams from Home Assistant.

It provides:

- a local Home Assistant browser player;
- a compact Lovelace dashboard card;
- a sidebar launcher that opens the full player in a new browser tab;
- station artwork, descriptions, genre, listeners, DJ and now-playing metadata when SomaFM provides it;
- selectable stream quality / bitrate;
- automatic reconnect logic for long listening sessions.

Current version: **v0.9.1**

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


## HACS installation

Safe SomaFM can be installed through HACS as a custom repository.

### Add as a custom repository

1. Open **HACS** in Home Assistant.
2. Open the top-right menu.
3. Select **Custom repositories**.
4. Add your GitHub repository URL.
5. Select category:

```text
Integration
```

6. Click **Add**.
7. Search for **Safe SomaFM** in HACS.
8. Download it.
9. Restart Home Assistant.
10. Go to **Settings → Devices & services → Add integration** and add **Safe SomaFM**.

### Lovelace card resource

After installing through HACS, add this dashboard resource if it is not added automatically:

```text
/safe_somafm/card.js
```

Resource type:

```text
JavaScript module
```

Then use:

```yaml
type: custom:safe-somafm-card
title: Safe SomaFM
height: 320px
```

### Sidebar launcher

After a full Home Assistant restart, the **Safe SomaFM** sidebar item should appear. It opens the full player in a new browser tab.

If it does not appear immediately, refresh the browser with `Ctrl + F5`.

## HACS readiness

This repository includes:

```text
hacs.json
.github/workflows/hacs.yml
.github/workflows/hassfest.yml
custom_components/safe_somafm/brand/icon.png
```

The HACS workflow validates the repository as an `integration`, and Hassfest validates the Home Assistant integration metadata.

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


## v0.8.4 station index visibility fix

This version restores the station index/grid visibility on the full player page while keeping the Lovelace dashboard card compact.

- `/safe_somafm/player` keeps the full station grid.
- `/safe_somafm/player?compact=1` keeps the compact dashboard layout.
- No playback or reconnect logic was changed.


## GitHub Pages index

This repository includes a simple `index.html` page for GitHub Pages.

It links to:

- the English README;
- the French README;
- the security review.

The Home Assistant integration itself does not depend on this file. It is only for the GitHub project page.


## v0.9.1 HACS folder structure fix

This version verifies that Home Assistant brand assets are stored in the correct location:

```text
custom_components/safe_somafm/brand/
```

There must not be a standalone folder named:

```text
custom_components/brand/
```

If `custom_components/brand/` exists, HACS may treat it as a separate integration and report:

```text
No manifest.json file found 'custom_components/brand/manifest.json'
```
