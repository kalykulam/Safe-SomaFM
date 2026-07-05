# Safe SomaFM for Home Assistant

A deliberately small Home Assistant media source for SomaFM stations.

## Security design

This integration is intentionally constrained:

- no credentials, tokens, cookies, or secrets
- no dynamic imports
- no shell commands or subprocesses
- no local file reads or writes
- no inbound HTTP server, webhook, or callback endpoint
- no third-party Python requirements
- outbound HTTP requests are limited to validated `https://*.somafm.com` URLs
- station identifiers are restricted to ASCII letters, digits, `_`, and `-`
- remote XML and playlist files have strict size limits
- XML containing `DOCTYPE` or `ENTITY` declarations is rejected before parsing
- playlists are accepted only if they resolve to `http://*.somafm.com` or `https://*.somafm.com` stream URLs

## What it does

It exposes SomaFM stations in Home Assistant's Media Browser via the `media_source` platform.
You can browse SomaFM stations and play them on supported media players.

## Installation

Manual installation:

1. Copy `custom_components/safe_somafm` into your Home Assistant configuration directory:
   `/config/custom_components/safe_somafm`
2. Restart Home Assistant.
3. Go to **Settings > Devices & services > Add integration**.
4. Search for **Safe SomaFM** and add it.
5. Open **Media Browser** and select **Safe SomaFM**.

HACS custom repository:

1. Put this repository on GitHub.
2. In HACS, add it as a custom repository of type **Integration**.
3. Install it, restart Home Assistant, then add the integration from the UI.

## Files

```text
custom_components/safe_somafm/
  __init__.py
  somafm.py
  config_flow.py
  const.py
  manifest.json
  media_source.py
  strings.json
hacs.json
README.md
```

## Notes

This code cannot prove that Home Assistant itself, HACS, your network, or SomaFM are risk-free. It only minimizes the integration's own attack surface and makes the behavior easy to audit.

## Version 0.1.1

Fixes catalog loading with the current SomaFM `channels.xml` schema. SomaFM exposes playlist URLs through tags such as `highestpls` and `fastpls`; version 0.1.0 only looked for a legacy `pls` tag.

## Support

[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-support-yellow?logo=buymeacoffee)](https://buymeacoffee.com/kalykulam)
