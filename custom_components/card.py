"""Lovelace card endpoint for Safe SomaFM."""

from __future__ import annotations

from aiohttp import web
from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant


_CARD_PATH = "/safe_somafm/card.js"


_CARD_JS = r"""
class SafeSomaFMCard extends HTMLElement {
  setConfig(config) {
    this.config = {
      title: "Safe SomaFM",
      height: "320px",
      url: "/safe_somafm/player?compact=1",
      show_header: true,
      ...config,
    };
    this.render();
  }

  set hass(hass) {
    this._hass = hass;
  }

  getCardSize() {
    return 8;
  }

  render() {
    if (!this.shadowRoot) {
      this.attachShadow({ mode: "open" });
    }

    const title = this.escapeHtml(this.config.title || "Safe SomaFM");
    const height = this.sanitizeHeight(this.config.height || "720px");
    const url = this.sanitizeUrl(this.config.url || "/safe_somafm/player?compact=1");
    const showHeader = this.config.show_header !== false;

    this.shadowRoot.innerHTML = `
      <ha-card>
        <style>
          :host { display: block; }
          .header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            padding: 16px 16px 10px;
          }
          .title {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 1.05rem;
            font-weight: 700;
            color: var(--primary-text-color);
          }
          .icon {
            width: 34px;
            height: 34px;
            border-radius: 10px;
            display: grid;
            place-items: center;
            background: linear-gradient(135deg, #22c55e, #38bdf8);
            color: #07111f;
            flex: 0 0 auto;
          }
          .icon svg { width: 24px; height: 24px; }
          .open {
            border: 1px solid var(--divider-color, rgba(127,127,127,.35));
            border-radius: 999px;
            padding: 7px 11px;
            color: var(--primary-text-color);
            text-decoration: none;
            font-size: .86rem;
            background: var(--secondary-background-color, transparent);
          }
          .frame-wrap {
            overflow: hidden;
            border-radius: ${showHeader ? "0 0 var(--ha-card-border-radius, 12px) var(--ha-card-border-radius, 12px)" : "var(--ha-card-border-radius, 12px)"};
          }
          iframe {
            width: 100%;
            height: ${height};
            border: 0;
            display: block;
            background: var(--primary-background-color);
          }
        </style>
        ${showHeader ? `
        <div class="header">
          <div class="title">
            <span class="icon" aria-hidden="true">
              <svg viewBox="0 0 128 128">
                <circle cx="64" cy="64" r="31" fill="currentColor" opacity=".95"></circle>
                <circle cx="64" cy="64" r="12" fill="#22c55e"></circle>
                <path d="M30 48c-10 10-10 22 0 32M98 48c10 10 10 22 0 32M18 36c-18 18-18 38 0 56M110 36c18 18 18 38 0 56" fill="none" stroke="currentColor" stroke-width="8" stroke-linecap="round"></path>
              </svg>
            </span>
            <span>${title}</span>
          </div>
          <a class="open" href="${url}" target="_blank" rel="noreferrer">Open</a>
        </div>` : ""}
        <div class="frame-wrap">
          <iframe
            src="${url}"
            title="${title}"
            loading="lazy"
            allow="autoplay"
            referrerpolicy="same-origin"
          ></iframe>
        </div>
      </ha-card>
    `;
  }

  sanitizeUrl(url) {
    if (typeof url !== "string") {
      return "/safe_somafm/player?compact=1";
    }
    if (url.startsWith("/safe_somafm/player")) {
      return url;
    }
    return "/safe_somafm/player?compact=1";
  }

  sanitizeHeight(height) {
    if (typeof height === "number") {
      return `${Math.max(240, Math.min(1600, height))}px`;
    }
    if (typeof height !== "string") {
      return "320px";
    }
    const trimmed = height.trim();
    if (/^\d{3,4}px$/.test(trimmed)) {
      const px = Number.parseInt(trimmed, 10);
      return `${Math.max(240, Math.min(1600, px))}px`;
    }
    if (/^\d{2,3}vh$/.test(trimmed)) {
      const vh = Number.parseInt(trimmed, 10);
      return `${Math.max(40, Math.min(100, vh))}vh`;
    }
    return "320px";
  }

  escapeHtml(value) {
    return String(value).replace(/[&<>"']/g, (char) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#039;",
    }[char]));
  }
}

customElements.define("safe-somafm-card", SafeSomaFMCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "safe-somafm-card",
  name: "Safe SomaFM Card",
  description: "Embeds the Safe SomaFM local Home Assistant player.",
  preview: true,
});
"""


def async_register_card_view(hass: HomeAssistant) -> None:
    """Register the Lovelace card JavaScript endpoint."""
    hass.http.register_view(SafeSomaFMCardView(hass))


class SafeSomaFMCardView(HomeAssistantView):
    """Serve the Lovelace card JavaScript."""

    url = _CARD_PATH
    name = "safe_somafm:card"
    requires_auth = False

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the card view."""
        self.hass = hass

    async def get(self, request: web.Request) -> web.Response:
        """Serve card JavaScript."""
        return web.Response(
            text=_CARD_JS,
            content_type="application/javascript",
            headers={"Cache-Control": "no-store, max-age=0"},
        )
