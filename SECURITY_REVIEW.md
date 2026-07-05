# Security review notes

## Threat model

The integration runs inside Home Assistant, so any custom integration should be treated as trusted code. This implementation reduces risk by keeping the code small and removing unnecessary capabilities.

## Explicitly absent behaviors

Search these terms in the codebase; they should not appear in runtime code:

- `subprocess`
- `os.system`
- `eval`
- `exec`
- `open(`
- `socket`
- `pickle`
- `yaml.load`
- `importlib`
- `requests`
- `write`

## Network behavior

Expected outbound requests:

1. `GET https://somafm.com/channels.xml`
2. `GET https://*.somafm.com/*.pls`
3. The selected media player then receives a SomaFM stream URL under `*.somafm.com`.

No inbound network listener is created by this integration.

## Remaining risk

If SomaFM itself is compromised, the integration could receive malicious catalog or playlist data. Defensive checks reject oversized data, unsafe XML declarations, unknown station identifiers, non-SomaFM hosts, credential-bearing URLs, and unsupported URL schemes.

## Review update for 0.1.1

The station parser now accepts SomaFM's documented playlist tags such as `highestpls` and `fastpls`, while preserving the same restrictions:

- playlist URLs must be HTTPS;
- playlist URLs must be hosted on `somafm.com` or one of its subdomains;
- playlist URLs must end with `.pls`;
- stream URLs must use HTTP or HTTPS;
- stream URLs must be hosted on `somafm.com` or one of its subdomains;
- URLs with embedded usernames or passwords are rejected.
