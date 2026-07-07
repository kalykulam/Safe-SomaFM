"""Sidebar launcher panel for Safe SomaFM."""

from __future__ import annotations

import logging

from aiohttp import web
from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

_PANEL_JS_PATH = "/safe_somafm/panel.js"
_PANEL_URL_PATH = "safe-somafm"


_PANEL_JS = r"""
class SafeSomaFMPanel extends HTMLElement {
  connectedCallback() {
    if (!this.shadowRoot) {
      this.attachShadow({ mode: "open" });
    }
    this.render();
    this.openPlayerTab();
  }

  set hass(hass) {
    this._hass = hass;
  }

  set narrow(narrow) {
    this._narrow = narrow;
  }

  set panel(panel) {
    this._panel = panel;
  }

  openPlayerTab() {
    const url = "/safe_somafm/player";
    let opened = null;
    try {
      opened = window.open(url, "_blank", "noopener,noreferrer");
    } catch (err) {
      opened = null;
    }

    const status = this.shadowRoot?.getElementById("status");
    if (opened && status) {
      status.textContent = "Safe SomaFM has been opened in a new tab.";
    } else if (status) {
      status.textContent = "Your browser blocked the automatic new tab. Use the button below.";
    }
  }

  render() {
    if (!this.shadowRoot) {
      return;
    }
    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: grid;
          place-items: center;
          min-height: calc(100vh - var(--header-height, 0px));
          padding: 24px;
          box-sizing: border-box;
          background: var(--primary-background-color);
          color: var(--primary-text-color);
        }
        .card {
          width: min(460px, 100%);
          border-radius: var(--ha-card-border-radius, 16px);
          background: var(--card-background-color);
          box-shadow: var(--ha-card-box-shadow, 0 2px 8px rgba(0,0,0,.18));
          border: 1px solid var(--divider-color, rgba(127,127,127,.25));
          padding: 22px;
          text-align: center;
        }
        .icon {
          width: 72px;
          height: 72px;
          margin: 0 auto 14px;
          border-radius: 20px;
          display: grid;
          place-items: center;
          background: linear-gradient(135deg, #22c55e, #38bdf8);
          color: #07111f;
        }
        .icon svg {
          width: 50px;
          height: 50px;
        }
        h1 {
          margin: 0 0 8px;
          font-size: 1.35rem;
        }
        p {
          color: var(--secondary-text-color);
          line-height: 1.45;
          margin: 0 0 16px;
        }
        a.button {
          display: inline-flex;
          justify-content: center;
          align-items: center;
          min-height: 42px;
          padding: 0 18px;
          border-radius: 999px;
          background: linear-gradient(135deg, #22c55e, #38bdf8);
          color: #07111f;
          font-weight: 800;
          text-decoration: none;
        }
        #status {
          margin-top: 14px;
          font-size: .9rem;
          color: var(--secondary-text-color);
        }
      </style>
      <div class="card">
        <div class="icon" aria-hidden="true">
          <svg viewBox="0 0 128 128">
            <circle cx="64" cy="64" r="31" fill="currentColor" opacity=".95"></circle>
            <circle cx="64" cy="64" r="12" fill="#22c55e"></circle>
            <path d="M30 48c-10 10-10 22 0 32M98 48c10 10 10 22 0 32M18 36c-18 18-18 38 0 56M110 36c18 18 18 38 0 56" fill="none" stroke="currentColor" stroke-width="8" stroke-linecap="round"></path>
          </svg>
        </div>
        <h1>Safe SomaFM</h1>
        <p>The full player is intended to run in its own browser tab.</p>
        <a class="button" href="/safe_somafm/player" target="_blank" rel="noopener noreferrer">Open Safe SomaFM</a>
        <div id="status">Opening Safe SomaFM in a new tab...</div>
      </div>
    `;
  }
}

customElements.define("safe-somafm-panel", SafeSomaFMPanel);
"""


def async_register_sidebar_panel(hass: HomeAssistant) -> None:
    """Register Safe SomaFM in the Home Assistant sidebar."""
    hass.http.register_view(SafeSomaFMPanelJsView(hass))

    try:
        from homeassistant.components.frontend import async_register_built_in_panel

        async_register_built_in_panel(
            hass,
            component_name="custom",
            sidebar_title="Safe SomaFM",
            sidebar_icon="mdi:radio-tower",
            frontend_url_path=_PANEL_URL_PATH,
            config={
                "_panel_custom": {
                    "name": "safe-somafm-panel",
                    "module_url": _PANEL_JS_PATH,
                    "embed_iframe": True,
                }
            },
            require_admin=False,
        )
    except Exception as err:  # noqa: BLE001 - sidebar panel is optional.
        _LOGGER.warning("Could not register Safe SomaFM sidebar panel: %s", err)


class SafeSomaFMPanelJsView(HomeAssistantView):
    """Serve the sidebar panel JavaScript."""

    url = _PANEL_JS_PATH
    name = "safe_somafm:panel_js"
    requires_auth = False

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the panel JS view."""
        self.hass = hass

    async def get(self, request: web.Request) -> web.Response:
        """Serve panel JavaScript."""
        return web.Response(
            text=_PANEL_JS,
            content_type="application/javascript",
            headers={"Cache-Control": "no-store, max-age=0"},
        )
