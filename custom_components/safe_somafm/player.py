"""Local browser player for Safe SomaFM."""

from __future__ import annotations

from typing import Any

from aiohttp import web
from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant

from .const import DOMAIN, NAME, VERSION
from .somafm import QUALITY_AUTO, SafeSomaFMClient, SomaFMError, SomaFMValidationError


_PLAYER_PATH = "/safe_somafm/player"
_STATIONS_PATH = "/safe_somafm/stations"
_RESOLVE_PATH = "/safe_somafm/resolve/{station_id}"


_PLAYER_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>@@TITLE@@</title>
  <meta name="theme-color" content="#111827">
  <link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 128 128'%3E%3Crect width='128' height='128' rx='28' fill='%23111827'/%3E%3Ccircle cx='64' cy='64' r='34' fill='%2322c55e' opacity='.92'/%3E%3Ccircle cx='64' cy='64' r='16' fill='%23111827'/%3E%3Cpath d='M28 48c-10 10-10 22 0 32M100 48c10 10 10 22 0 32M16 36c-18 18-18 38 0 56M112 36c18 18 18 38 0 56' fill='none' stroke='%23e5e7eb' stroke-width='8' stroke-linecap='round'/%3E%3C/svg%3E">
  <style>
    :root { color-scheme: light dark; font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; --bg:#0f172a; --panel:rgba(15,23,42,.78); --panel-2:rgba(30,41,59,.72); --text:#f8fafc; --muted:#cbd5e1; --soft:rgba(148,163,184,.22); --accent:#22c55e; --accent-2:#38bdf8; --border:rgba(148,163,184,.28); --shadow:rgba(0,0,0,.28); }
    @media (prefers-color-scheme: light) { :root { --bg:#f8fafc; --panel:rgba(255,255,255,.90); --panel-2:rgba(241,245,249,.92); --text:#0f172a; --muted:#475569; --soft:rgba(15,23,42,.08); --border:rgba(15,23,42,.14); --shadow:rgba(15,23,42,.12); } }
    * { box-sizing: border-box; }
    body { margin:0; min-height:100vh; background: radial-gradient(circle at top left, rgba(56,189,248,.18), transparent 34rem), radial-gradient(circle at top right, rgba(34,197,94,.16), transparent 32rem), var(--bg); color:var(--text); }
    main { width:min(1180px,100%); margin:0 auto; padding:20px; }
    .app { display:grid; gap:18px; }
    .hero { display:grid; grid-template-columns:auto 1fr; gap:16px; align-items:center; padding:18px; border:1px solid var(--border); border-radius:22px; background:var(--panel); box-shadow:0 20px 60px var(--shadow); backdrop-filter:blur(12px); }
    .app-icon { width:64px; height:64px; border-radius:18px; display:grid; place-items:center; background:linear-gradient(135deg,var(--accent),var(--accent-2)); box-shadow:0 12px 32px rgba(34,197,94,.22); }
    .app-icon svg { width:44px; height:44px; }
    h1 { margin:0; font-size:clamp(1.35rem,3vw,2rem); letter-spacing:-.03em; }
    .subtitle { margin:4px 0 0; color:var(--muted); line-height:1.4; }
    .toolbar { display:grid; grid-template-columns:minmax(180px,1.4fr) minmax(160px,.8fr) minmax(160px,.8fr); gap:12px; padding:14px; border:1px solid var(--border); border-radius:18px; background:var(--panel); backdrop-filter:blur(12px); position:sticky; top:0; z-index:10; }
    label { display:block; margin:0 0 6px; font-size:.78rem; color:var(--muted); font-weight:700; text-transform:uppercase; letter-spacing:.06em; }
    select, input, button { font:inherit; width:100%; border-radius:12px; padding:11px 12px; border:1px solid var(--border); background:var(--panel-2); color:var(--text); }
    button { cursor:pointer; font-weight:800; transition:transform .12s ease, border-color .12s ease; }
    button:hover { transform:translateY(-1px); border-color:rgba(34,197,94,.72); }
    .button-row { display:grid; grid-template-columns:1fr 1fr; gap:10px; }
    .play-button { background:linear-gradient(135deg,rgba(34,197,94,.92),rgba(56,189,248,.82)); color:#06111f; border-color:transparent; }
    .now { display:grid; grid-template-columns:116px 1fr; gap:16px; align-items:start; padding:16px; border:1px solid var(--border); border-radius:22px; background:var(--panel); backdrop-filter:blur(12px); }
    .cover { width:116px; height:116px; object-fit:cover; border-radius:18px; border:1px solid var(--border); background:var(--soft); }
    .now h2 { margin:0 0 6px; font-size:1.35rem; }
    .description { margin:8px 0 0; color:var(--muted); line-height:1.45; }
    .chips { display:flex; flex-wrap:wrap; gap:8px; margin:10px 0; }
    .chip { display:inline-flex; border-radius:999px; padding:6px 10px; background:var(--soft); font-size:.86rem; color:var(--text); }
    audio { width:100%; margin-top:12px; }
    .status { margin-top:12px; padding:10px 12px; border-radius:12px; background:var(--soft); color:var(--muted); font-size:.92rem; white-space:pre-wrap; }
    .section-title { display:flex; align-items:baseline; justify-content:space-between; gap:12px; }
    .section-title h2 { margin:0; font-size:1.2rem; }
    .count { color:var(--muted); font-size:.92rem; }
    .grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(190px,1fr)); gap:14px; }
    .station-card { display:grid; gap:10px; text-align:left; padding:12px; border:1px solid var(--border); border-radius:18px; background:var(--panel); color:var(--text); min-height:100%; box-shadow:0 10px 26px rgba(0,0,0,.10); }
    .station-card.active { outline:3px solid rgba(34,197,94,.55); border-color:rgba(34,197,94,.78); }
    .station-image { width:100%; aspect-ratio:1/1; object-fit:cover; border-radius:14px; background:var(--soft); border:1px solid var(--border); }
    .station-name { font-weight:850; font-size:1rem; line-height:1.15; }
    .station-meta { color:var(--muted); font-size:.85rem; line-height:1.3; }
    .station-desc { color:var(--muted); font-size:.86rem; line-height:1.35; display:-webkit-box; -webkit-line-clamp:3; -webkit-box-orient:vertical; overflow:hidden; }
    .hidden { display:none !important; }
    @media (max-width:820px) { main{padding:12px}.toolbar{position:static;grid-template-columns:1fr}.now{grid-template-columns:1fr}.cover{width:96px;height:96px}.hero{grid-template-columns:1fr} }

    body.compact-mode main {
      padding: 0;
      width: 100%;
    }
    body.compact-mode .app {
      gap: 10px;
    }
    body.compact-mode .hero {
      display: none;
    }
    body.compact-mode .toolbar {
      position: static;
      grid-template-columns: 1fr;
      padding: 7px;
      border-radius: 12px;
      background: transparent;
      border: 0;
    }
    body.compact-mode .toolbar label {
      font-size: .70rem;
      margin-bottom: 4px;
    }
    body.compact-mode select,
    body.compact-mode input,
    body.compact-mode button {
      padding: 8px 10px;
      border-radius: 9px;
      font-size: .9rem;
    }
    body.compact-mode .now {
      grid-template-columns: 56px 1fr;
      gap: 8px;
      padding: 7px;
      border-radius: 12px;
      background: var(--panel);
    }
    body.compact-mode .cover {
      width: 56px;
      height: 56px;
      border-radius: 12px;
    }
    body.compact-mode .now h2 {
      font-size: 1rem;
      margin-bottom: 4px;
    }
    body.compact-mode .description {
      font-size: .82rem;
      line-height: 1.3;
      margin-top: 4px;
    }
    body.compact-mode .chips {
      margin: 5px 0;
      gap: 5px;
    }
    body.compact-mode .chip {
      font-size: .72rem;
      padding: 4px 7px;
    }
    body.compact-mode audio {
      margin-top: 8px;
      height: 32px;
    }
    body.compact-mode .status {
      font-size: .78rem;
      padding: 7px 9px;
      margin-top: 8px;
    }
    body.compact-mode .section-title {
      padding: 0 10px;
    }
    body.compact-mode .section-title h2 {
      font-size: .98rem;
    }
    body.compact-mode .count {
      font-size: .78rem;
    }
    body.compact-mode .grid {
      grid-template-columns: repeat(auto-fill, minmax(64px, 1fr));
      gap: 8px;
      padding: 0 10px 10px;
    }
    body.compact-mode .station-card {
      padding: 5px;
      gap: 4px;
      border-radius: 10px;
    }
    body.compact-mode .station-image {
      width: min(100%, 42px);
      justify-self: center;
      border-radius: 10px;
    }
    body.compact-mode .station-name {
      font-size: .66rem;
      line-height: 1.02;
      text-align: center;
      word-break: normal;
    }
    body.compact-mode .station-meta,
    body.compact-mode .station-desc {
      display: none;
    }
    body.compact-mode #stationDescription {
      display: none;
    }


    body.compact-mode .now {
      grid-template-columns: 54px 1fr;
    }
    body.compact-mode .cover {
      width: 54px;
      height: 54px;
    }
    body.compact-mode .now h2 {
      font-size: .92rem;
    }
    body.compact-mode .chips,
    body.compact-mode #stationNowPlaying {
      display: none;
    }
    body.compact-mode .toolbar {
      gap: 8px;
    }
    body.compact-mode .button-row {
      gap: 6px;
    }


    body.compact-mode .grid { display: grid; }
    body.compact-mode .section-title { display: flex; }
    body.full-mode .grid { display: grid; }

  </style>
</head>
<body>
  <main><div class="app">
    <section class="hero"><div class="app-icon" aria-hidden="true"><svg viewBox="0 0 128 128"><circle cx="64" cy="64" r="31" fill="#07111f"></circle><circle cx="64" cy="64" r="13" fill="#22c55e"></circle><path d="M30 48c-10 10-10 22 0 32M98 48c10 10 10 22 0 32M18 36c-18 18-18 38 0 56M110 36c18 18 18 38 0 56" fill="none" stroke="#f8fafc" stroke-width="8" stroke-linecap="round"></path></svg></div><div><h1>@@TITLE@@</h1><p class="subtitle">v@@VERSION@@</p></div></section>
    <section class="toolbar"><div><label for="search">Search stations</label><input id="search" type="search" placeholder="Search by name, genre, description..."></div><div><label for="quality">Quality / bitrate</label><select id="quality"><option value="auto">Auto (recommended)</option></select></div><div><label>Playback</label><div class="button-row"><button id="play" class="play-button">Play</button><button id="stop">Stop</button></div></div></section>
    <section class="now"><img id="stationImage" class="cover" alt="" loading="lazy"><div><h2 id="stationTitle">Loading stations...</h2><div id="stationChips" class="chips"></div><p id="stationDescription" class="description"></p><div id="stationNowPlaying" class="description hidden"><strong>Now playing: </strong><span id="stationNowPlayingText"></span></div><audio id="audio" controls preload="none"></audio><div id="status" class="status">Idle</div></div></section>
    <section><div class="section-title"><h2 id="stationsTitle">Stations</h2><div id="count" class="count"></div></div><div id="stationGrid" class="grid"></div></section>
  </div></main>
<script>
(() => {
  const params = new URLSearchParams(window.location.search);
  const compactMode = params.get('compact') === '1' || params.get('mode') === 'compact';
  document.body.classList.add(compactMode ? 'compact-mode' : 'full-mode');

  const qualitySelect=document.getElementById('quality'), playButton=document.getElementById('play'), stopButton=document.getElementById('stop'), audio=document.getElementById('audio'), status=document.getElementById('status'), searchInput=document.getElementById('search'), stationGrid=document.getElementById('stationGrid'), count=document.getElementById('count'), stationImage=document.getElementById('stationImage'), stationTitle=document.getElementById('stationTitle'), stationChips=document.getElementById('stationChips'), stationDescription=document.getElementById('stationDescription'), stationNowPlaying=document.getElementById('stationNowPlaying'), stationNowPlayingText=document.getElementById('stationNowPlayingText');
  let currentStation=null, stations=[], intentionalStop=false, reconnectTimer=null, watchdogTimer=null, lastTime=0, lastAdvance=Date.now();
  function setStatus(message){const stamp=new Date().toLocaleTimeString();status.textContent=`[${stamp}] ${message}`;}
  async function fetchJson(url){const response=await fetch(url,{credentials:'same-origin'}); if(!response.ok) throw new Error(`HTTP ${response.status}`); return await response.json();}
  function selectedStation(){return stations.find((item)=>item.id===currentStation)||null;}
  function clearChildren(node){while(node.firstChild) node.removeChild(node.firstChild);}
  function addChip(label,value){if(value===undefined||value===null||value==='') return; const chip=document.createElement('span'); chip.className='chip'; chip.textContent=`${label}: ${value}`; stationChips.appendChild(chip);}
  function imageFor(station){return station?.large_thumbnail||station?.thumbnail||'';}
  function updateStationInfo(){const station=selectedStation(); if(!station) return; stationTitle.textContent=station.title||station.id; stationDescription.textContent=station.description||''; const image=imageFor(station); if(image){stationImage.src=image; stationImage.alt=station.title?`${station.title} logo`:'Station logo';} else {stationImage.removeAttribute('src'); stationImage.alt='';} clearChildren(stationChips); addChip('Genre',station.genre); addChip('Listeners',station.listeners); addChip('DJ',station.dj); if(station.last_playing){stationNowPlaying.classList.remove('hidden'); stationNowPlayingText.textContent=station.last_playing;} else {stationNowPlaying.classList.add('hidden'); stationNowPlayingText.textContent='';} populateQualityOptions(); highlightActiveCard();}
  function populateQualityOptions(){const station=selectedStation(); const previous=qualitySelect.value||'auto'; qualitySelect.innerHTML=''; const autoOption=document.createElement('option'); autoOption.value='auto'; autoOption.textContent='Auto (recommended)'; qualitySelect.appendChild(autoOption); for(const quality of station?.qualities||[]){const option=document.createElement('option'); option.value=quality.id; option.textContent=quality.label; qualitySelect.appendChild(option);} qualitySelect.value=[...qualitySelect.options].some((option)=>option.value===previous)?previous:'auto';}
  function stationMatchesSearch(station,query){if(!query) return true; const haystack=[station.title,station.genre,station.description,station.dj,station.last_playing].filter(Boolean).join(' ').toLowerCase(); return haystack.includes(query);}
  function shortText(text,maxLength){if(!text||text.length<=maxLength) return text||''; return `${text.slice(0,maxLength-1).trim()}...`;}
  function renderGrid(){const query=searchInput.value.trim().toLowerCase(); const visible=stations.filter((station)=>stationMatchesSearch(station,query)); stationGrid.innerHTML=''; for(const station of visible){const card=document.createElement('button'); card.className='station-card'; card.type='button'; card.dataset.stationId=station.id; const img=document.createElement('img'); img.className='station-image'; img.loading='lazy'; img.alt=station.title?`${station.title} logo`:''; const image=imageFor(station); if(image) img.src=image; const name=document.createElement('div'); name.className='station-name'; name.textContent=station.title||station.id; const meta=document.createElement('div'); meta.className='station-meta'; meta.textContent=[station.genre, station.listeners?`${station.listeners} listeners`:''].filter(Boolean).join(' - '); const desc=document.createElement('div'); desc.className='station-desc'; desc.textContent=shortText(station.description,150); card.appendChild(img); card.appendChild(name); if(meta.textContent) card.appendChild(meta); if(desc.textContent) card.appendChild(desc); card.addEventListener('click',()=>{currentStation=station.id; updateStationInfo(); resolveAndPlay('station card').catch((err)=>setStatus(`Play failed: ${err.message}`));}); stationGrid.appendChild(card);} count.textContent=`${visible.length} / ${stations.length} stations`; highlightActiveCard();}
  function highlightActiveCard(){for(const card of stationGrid.querySelectorAll('.station-card')) card.classList.toggle('active', card.dataset.stationId===currentStation);}
  async function loadStations(){const data=await fetchJson('@@STATIONS_PATH@@'); stations=data.stations||[]; if(stations.length){currentStation=stations[0].id; updateStationInfo(); renderGrid(); setStatus(`Loaded ${stations.length} stations.`);} else {setStatus('No station found.'); count.textContent='0 stations';}}
  async function resolveAndPlay(reason){clearTimeout(reconnectTimer); if(!currentStation&&stations.length) currentStation=stations[0].id; intentionalStop=false; updateStationInfo(); setStatus(`Resolving ${currentStation} (${reason})...`); const quality=qualitySelect.value||'auto'; const data=await fetchJson(`/safe_somafm/resolve/${encodeURIComponent(currentStation)}?quality=${encodeURIComponent(quality)}`); audio.src=data.url; audio.type=data.content_type||'audio/mpeg'; audio.load(); await audio.play(); lastTime=audio.currentTime||0; lastAdvance=Date.now(); setStatus(`Playing ${data.title} (${data.quality_label||quality}) via ${data.host}`); startWatchdog();}
  function scheduleReconnect(reason){if(intentionalStop||!currentStation) return; clearTimeout(reconnectTimer); setStatus(`Playback ${reason}. Reconnecting...`); reconnectTimer=setTimeout(()=>{resolveAndPlay(reason).catch((err)=>{setStatus(`Reconnect failed: ${err.message}. Retrying...`); scheduleReconnect('retry');});},1200);}
  function startWatchdog(){clearInterval(watchdogTimer); watchdogTimer=setInterval(()=>{if(audio.paused||audio.ended||intentionalStop) return; const now=Date.now(); const t=audio.currentTime||0; if(t>lastTime+.2){lastTime=t; lastAdvance=now; return;} if(now-lastAdvance>15000) scheduleReconnect('appears stalled');},5000);}
  playButton.addEventListener('click',()=>{resolveAndPlay('manual play').catch((err)=>setStatus(`Play failed: ${err.message}`));});
  stopButton.addEventListener('click',()=>{intentionalStop=true; clearTimeout(reconnectTimer); clearInterval(watchdogTimer); audio.pause(); audio.removeAttribute('src'); audio.load(); setStatus('Stopped.');});
  qualitySelect.addEventListener('change',()=>{if(!audio.paused) resolveAndPlay('quality changed').catch((err)=>setStatus(`Play failed: ${err.message}`));});
  searchInput.addEventListener('input',renderGrid);
  audio.addEventListener('ended',()=>scheduleReconnect('ended')); audio.addEventListener('error',()=>scheduleReconnect('errored')); audio.addEventListener('stalled',()=>scheduleReconnect('stalled')); audio.addEventListener('waiting',()=>setStatus('Buffering...')); audio.addEventListener('playing',()=>{const station=selectedStation(); setStatus(`Playing ${station?.title||currentStation}`);});
  loadStations().catch((err)=>setStatus(`Could not load stations: ${err.message}`));
})();
</script>
</body>
</html>
"""


def _client_from_hass(hass: HomeAssistant) -> SafeSomaFMClient:
    """Return the configured Safe SomaFM client."""
    entries = hass.config_entries.async_entries(DOMAIN)
    if not entries:
        raise SomaFMError("Safe SomaFM is not configured")
    return entries[0].runtime_data


def async_register_player_views(hass: HomeAssistant) -> None:
    """Register local HTTP views used by the browser player."""
    hass.http.register_view(SafeSomaFMPlayerView(hass))
    hass.http.register_view(SafeSomaFMStationsView(hass))
    hass.http.register_view(SafeSomaFMResolveView(hass))


class SafeSomaFMPlayerView(HomeAssistantView):
    """Serve a small browser player page."""

    url = _PLAYER_PATH
    name = "safe_somafm:player"
    requires_auth = False

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the player view."""
        self.hass = hass

    async def get(self, request: web.Request) -> web.Response:
        """Serve the local player page."""
        body = (_PLAYER_HTML.replace("@@TITLE@@", NAME).replace("@@VERSION@@", VERSION).replace("@@STATIONS_PATH@@", _STATIONS_PATH))
        return web.Response(text=body, content_type="text/html", headers={"Cache-Control": "no-store, max-age=0"})


class SafeSomaFMStationsView(HomeAssistantView):
    """Return the validated station list as JSON."""

    url = _STATIONS_PATH
    name = "safe_somafm:stations"
    requires_auth = False

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the station API view."""
        self.hass = hass

    async def get(self, request: web.Request) -> web.Response:
        """Return stations."""
        client = _client_from_hass(self.hass)
        stations = await client.async_get_stations()
        payload: dict[str, Any] = {
            "stations": [
                {
                    "id": station.station_id,
                    "title": station.title,
                    "description": station.description,
                    "thumbnail": station.image_url,
                    "large_thumbnail": station.large_image_url,
                    "genre": station.genre,
                    "dj": station.dj,
                    "listeners": station.listeners,
                    "last_playing": station.last_playing,
                    "qualities": [{"id": option.quality_id, "label": option.label} for option in station.stream_options],
                }
                for station in stations.values()
            ]
        }
        return web.json_response(payload)


class SafeSomaFMResolveView(HomeAssistantView):
    """Resolve a station to a fresh direct stream URL for the browser player."""

    url = _RESOLVE_PATH
    name = "safe_somafm:resolve"
    requires_auth = False

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the resolve API view."""
        self.hass = hass

    async def get(self, request: web.Request, station_id: str) -> web.Response:
        """Resolve a station."""
        client = _client_from_hass(self.hass)
        try:
            station = (await client.async_get_stations()).get(station_id)
            quality_id = request.query.get("quality", QUALITY_AUTO)
            resolved = await client.async_resolve_station(station_id, quality_id)
        except SomaFMValidationError as err:
            return web.json_response({"error": str(err)}, status=404)
        except SomaFMError as err:
            return web.json_response({"error": str(err)}, status=502)

        title = station.title if station is not None else station_id
        from urllib.parse import urlparse

        parsed = urlparse(resolved.url)
        return web.json_response({"id": station_id, "title": title, "url": resolved.url, "content_type": resolved.content_type, "quality_id": resolved.quality_id, "quality_label": resolved.quality_label, "host": parsed.hostname})
