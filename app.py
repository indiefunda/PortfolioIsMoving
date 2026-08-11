#!/usr/bin/env python3
"""
PortfolioIsMoving - local setup app.

Starts a tiny local web server and opens your browser at
http://localhost:8000 where you can:
  - Add / remove tickers
  - Set the movement threshold (%)
  - Enter your Telegram bot token and chat id
  - Enable / disable monitoring
  - Test that Telegram alerts work

Everything is saved to local files. Nothing is uploaded. Close the window
when you're done - monitoring runs 24/7 in the cloud via GitHub Actions.

Uses only the Python standard library (http.server, json, webbrowser).
"""

import json
import os
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config_local.json")
SECRETS_FILE = os.path.join(BASE_DIR, "secrets_local.json")
STATE_FILE = os.path.join(BASE_DIR, "state.json")

PORT = 8000

DEFAULT_CONFIG = {
    "tickers": [],
    "threshold_pct": 5.0,
    "enabled": False,
    "provider": "twelvedata",  # twelvedata (default) | finnhub | yahoo
}

# ---------------------------------------------------------------------------
# File helpers
# ---------------------------------------------------------------------------
def _read_json(path, default):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(default, dict) and isinstance(data, dict):
                merged = dict(default)
                merged.update(data)
                return merged
            return data
        except Exception:
            return default
    return default


def _write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_config():
    return _read_json(CONFIG_FILE, dict(DEFAULT_CONFIG))


def save_config(config):
    _write_json(CONFIG_FILE, config)


def load_secrets():
    return _read_json(SECRETS_FILE, {"telegram_bot_token": "", "telegram_chat_id": "", "price_api_key": ""})


def save_secrets(secrets):
    _write_json(SECRETS_FILE, secrets)


# ---------------------------------------------------------------------------
# Telegram test
# ---------------------------------------------------------------------------
def send_telegram(token, chat_id, message):
    import requests
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        resp = requests.post(url, data={"chat_id": chat_id, "text": message}, timeout=15)
        resp.raise_for_status()
        return True, "OK"
    except Exception as exc:
        return False, str(exc)


# ---------------------------------------------------------------------------
# HTTP handler
# ---------------------------------------------------------------------------
class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # silence default logging

    def _send_json(self, obj, status=200):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html):
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/" or parsed.path == "/index.html":
            self._send_html(HTML)
        elif parsed.path == "/api/config":
            cfg = load_config()
            secrets = load_secrets()
            self._send_json({"config": cfg, "secrets": secrets})
        elif parsed.path == "/api/price":
            qs = parse_qs(parsed.query)
            symbol = (qs.get("symbol") or [""])[0].strip().upper()
            if not symbol:
                self._send_json({"error": "no symbol"}, 400)
                return
            import monitor
            cfg = load_config()
            secrets = load_secrets()
            provider = cfg.get("provider", "twelvedata")
            api_key = secrets.get("price_api_key", "")
            prices = monitor.get_prices([symbol], provider=provider, api_key=api_key)
            pair = prices.get(symbol)
            if pair is None:
                self._send_json({"error": f"Could not fetch {symbol} via {provider}"}, 502)
                return
            cur, prev = pair
            pct = ((cur - prev) / prev * 100.0) if prev else 0.0
            self._send_json({"symbol": symbol, "current": cur, "prev_close": prev, "pct": round(pct, 2)})
        else:
            self._send_json({"error": "not found"}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8") if length else "{}"
        try:
            payload = json.loads(body) if body else {}
        except Exception:
            payload = {}

        if parsed.path == "/api/save":
            cfg = load_config()
            secrets = load_secrets()
            if "tickers" in payload:
                cfg["tickers"] = [t.strip().upper() for t in payload["tickers"] if t.strip()]
            if "threshold_pct" in payload:
                try:
                    cfg["threshold_pct"] = float(payload["threshold_pct"])
                except Exception:
                    pass
            if "enabled" in payload:
                cfg["enabled"] = bool(payload["enabled"])
            if "provider" in payload:
                p = payload["provider"].strip().lower()
                if p in ("twelvedata", "finnhub", "yahoo"):
                    cfg["provider"] = p
            if "telegram_bot_token" in payload:
                secrets["telegram_bot_token"] = payload["telegram_bot_token"].strip()
            if "telegram_chat_id" in payload:
                secrets["telegram_chat_id"] = payload["telegram_chat_id"].strip()
            if "price_api_key" in payload:
                secrets["price_api_key"] = payload["price_api_key"].strip()
            save_config(cfg)
            save_secrets(secrets)
            self._send_json({"ok": True, "config": cfg})
        elif parsed.path == "/api/test":
            token = (payload.get("telegram_bot_token") or "").strip()
            chat_id = (payload.get("telegram_chat_id") or "").strip()
            if not token or not chat_id:
                self._send_json({"ok": False, "error": "Enter both token and chat id first."}, 400)
                return
            import monitor
            cfg = load_config()
            secrets = load_secrets()
            provider = cfg.get("provider", "twelvedata")
            api_key = secrets.get("price_api_key", "")
            tickers = cfg.get("tickers", [])
            symbol = tickers[0].strip().upper() if tickers else "AAPL"

            # Fetch a live price to include real stats in the test alert.
            prices = monitor.get_prices([symbol], provider=provider, api_key=api_key)
            pair = prices.get(symbol)

            if pair:
                cur, prev = pair
                pct = ((cur - prev) / prev * 100.0) if prev else 0.0
                arrow = "▲" if pct >= 0 else "▼"
                msg = (
                    f"✅ TEST ALERT (via {provider})\n"
                    f"{symbol} has moved {arrow} {abs(pct):.1f}% right now\n"
                    f"Price: ${cur:.2f}  |  Prev close: ${prev:.2f}\n"
                    f"Compared to the last trading day's close."
                )
            else:
                msg = (
                    f"✅ TEST ALERT (via {provider})\n"
                    f"Could not fetch {symbol} price — check your API key/provider.\n"
                    f"If this keeps failing, try switching provider in the setup page."
                )
            ok, err = send_telegram(token, chat_id, msg)
            self._send_json({"ok": ok, "error": err if not ok else None, "message": msg})
        else:
            self._send_json({"error": "not found"}, 404)


# ---------------------------------------------------------------------------
# HTML page (embedded)
# ---------------------------------------------------------------------------
HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PortfolioIsMoving</title>
<style>
  :root {
    --bg: #0f172a; --card: #1e293b; --border: #334155;
    --text: #e2e8f0; --muted: #94a3b8; --accent: #38bdf8;
    --green: #22c55e; --red: #ef4444; --amber: #f59e0b;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, "Segoe UI", Roboto, Arial, sans-serif;
    background: var(--bg); color: var(--text);
    min-height: 100vh; padding: 24px;
  }
  .wrap { max-width: 640px; margin: 0 auto; }
  h1 { font-size: 26px; margin-bottom: 4px; }
  .sub { color: var(--muted); font-size: 14px; margin-bottom: 24px; }
  .card {
    background: var(--card); border: 1px solid var(--border);
    border-radius: 12px; padding: 20px; margin-bottom: 20px;
  }
  .card h2 { font-size: 16px; margin-bottom: 14px; color: var(--accent); }
  label { display: block; font-size: 13px; color: var(--muted); margin-bottom: 6px; }
  input[type=text], input[type=number] {
    width: 100%; padding: 10px 12px; border-radius: 8px;
    border: 1px solid var(--border); background: var(--bg);
    color: var(--text); font-size: 14px;
  }
  input:focus { outline: 2px solid var(--accent); border-color: transparent; }
  select {
    width: 100%; padding: 10px 12px; border-radius: 8px;
    border: 1px solid var(--border); background: var(--bg);
    color: var(--text); font-size: 14px;
  }
  select:focus { outline: 2px solid var(--accent); border-color: transparent; }
  .row { display: flex; gap: 8px; margin-bottom: 12px; }
  .row input { flex: 1; }
  button {
    padding: 10px 16px; border-radius: 8px; border: none; cursor: pointer;
    font-size: 14px; font-weight: 600;
  }
  .btn-primary { background: var(--accent); color: #0f172a; }
  .btn-ghost { background: transparent; color: var(--text); border: 1px solid var(--border); }
  .btn-danger { background: transparent; color: var(--red); border: 1px solid var(--red); }
  button:hover { filter: brightness(1.1); }
  .chips { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px; }
  .chip {
    background: var(--bg); border: 1px solid var(--border);
    padding: 6px 12px; border-radius: 20px; font-size: 13px;
    display: inline-flex; align-items: center; gap: 8px;
  }
  .chip button { background: none; border: none; color: var(--red); cursor: pointer; font-size: 14px; padding: 0; }
  .switch { position: relative; display: inline-block; width: 52px; height: 28px; }
  .switch input { opacity: 0; width: 0; height: 0; }
  .slider {
    position: absolute; cursor: pointer; inset: 0;
    background: var(--border); border-radius: 28px; transition: .3s;
  }
  .slider:before {
    content: ""; position: absolute; height: 22px; width: 22px; left: 3px; bottom: 3px;
    background: #fff; border-radius: 50%; transition: .3s;
  }
  .switch input:checked + .slider { background: var(--green); }
  .switch input:checked + .slider:before { transform: translateX(24px); }
  .toggle-row { display: flex; align-items: center; justify-content: space-between; }
  .status { font-size: 13px; color: var(--muted); }
  .status.on { color: var(--green); font-weight: 600; }
  .status.off { color: var(--muted); }
  .msg { padding: 10px 14px; border-radius: 8px; margin-top: 12px; font-size: 13px; display: none; }
  .msg.ok { display: block; background: rgba(34,197,94,.12); color: var(--green); border: 1px solid rgba(34,197,94,.3); }
  .msg.err { display: block; background: rgba(239,68,68,.12); color: var(--red); border: 1px solid rgba(239,68,68,.3); }
  .price-preview { margin-top: 14px; font-size: 13px; color: var(--muted); }
  .price-preview .up { color: var(--green); }
  .price-preview .down { color: var(--red); }
  .hint { font-size: 12px; color: var(--muted); margin-top: 8px; line-height: 1.5; }
  .secret { font-family: monospace; }
  .guide-text { font-size: 14px; line-height: 1.7; color: var(--text); }
  .guide-text p { margin-bottom: 12px; }
  .guide-text ul, .guide-text ol { margin: 0 0 12px 20px; }
  .guide-text li { margin-bottom: 6px; }
  .guide-text code {
    background: var(--bg); padding: 2px 6px; border-radius: 4px;
    font-size: 13px; color: var(--accent);
  }
  .guide-text strong { color: var(--text); }
</style>
</head>
<body>
<div class="wrap">
  <div style="display:flex;align-items:center;justify-content:space-between">
    <div>
      <h1>📈 PortfolioIsMoving</h1>
      <div class="sub">Set up your portfolio. Monitoring runs free in the cloud 24/7.</div>
    </div>
    <button class="btn-ghost" onclick="toggleGuide()">❓ How it works</button>
  </div>

  <div class="card" id="guide" style="display:none">
    <h2>📖 How it works (read this first)</h2>
    <div class="guide-text">
      <p><strong>1. What this does.</strong> It watches your stocks during US market
      hours and sends you a <strong>Telegram message on your phone</strong> when a stock
      moves more than your chosen amount (default 5%) from the previous day's close.</p>

      <p><strong>2. You only set this up once.</strong> Fill in the 4 boxes below, click
      <strong>Save</strong>, and you're done. After that, monitoring runs free in the
      <strong>cloud</strong> 24/7 — your computer can be turned off.</p>

      <p><strong>3. The 4 boxes, explained:</strong></p>
      <ul>
        <li><strong>Your stocks</strong> — type a ticker (the short code for a stock,
        e.g. <code>HUIZ</code>, <code>AAPL</code>) and click Add. Add as many as you like.</li>
        <li><strong>Alert threshold</strong> — how big a move triggers an alert. 5 = alert
        when it moves more than 5%.</li>
        <li><strong>Telegram</strong> — how alerts reach your phone. You create a free bot
        once (see below) and paste its token + your chat id here.</li>
        <li><strong>Enable monitoring</strong> — the on/off switch. Turn it on when ready.</li>
      </ul>

      <p><strong>4. Setting up Telegram (free, 2 minutes):</strong></p>
      <ol>
        <li>Open <strong>Telegram</strong> on your phone.</li>
        <li>Search for <strong>@BotFather</strong> (official bot, blue checkmark).</li>
        <li>Send <code>/newbot</code>, pick a name, then a username ending in <code>bot</code>.</li>
        <li>BotFather gives you a <strong>token</strong> like <code>123456789:AAH...</code> — copy it.</li>
        <li>Open your new bot, press <strong>Start</strong>.</li>
        <li>In a browser go to
        <code>https://api.telegram.org/bot&lt;TOKEN&gt;/getUpdates</code> and find your
        <strong>chat id</strong> (a number inside <code>"chat":{"id":123}</code>).</li>
      </ol>

      <p><strong>5. To finish, connect to GitHub</strong> so it runs 24/7 for free.
      Open the <strong>README.md</strong> file in this folder and follow the
      "Connect to GitHub" section. It takes ~5 minutes, once.</p>

      <p><strong>6. Limitations (be honest with yourself):</strong></p>
      <ul>
        <li><strong>Delay depends on your data provider.</strong> Twelve Data and Finnhub
        are <strong>real-time</strong> (best). Yahoo is ~15 min delayed. All are free.</li>
        <li>Checks happen <strong>every 10 minutes</strong>, during US market hours
        (Mon–Fri, 9:30am–4pm Eastern).</li>
        <li>Each stock alerts <strong>once per day</strong> — you won't be spammed.</li>
        <li>It only works for stocks with a ticker on a US exchange.</li>
      </ul>

      <p><strong>7. If something isn't working:</strong></p>
      <ul>
        <li><strong>No browser opens?</strong> Manually go to <code>http://localhost:8000</code>.</li>
        <li><strong>"Python is not installed"?</strong> Install it from python.org and
        tick <strong>"Add Python to PATH"</strong> during install. Then run start.bat again.</li>
        <li><strong>Test alert doesn't arrive?</strong> Double-check the token and chat id
        are pasted exactly (no spaces). Make sure you pressed <strong>Start</strong> on your bot.</li>
        <li><strong>Test alert arrives but says "could not fetch price"?</strong> Your API key
        may be wrong, or the provider is down. Try switching the provider in the setup page.</li>
        <li><strong>No alerts during the day?</strong> Check your GitHub Actions log — see
        README. Common cause: you forgot to add the secrets, or monitoring is off.</li>
        <li><strong>Still stuck?</strong> Re-read the README step by step, or ask whoever
        gave you this app.</li>
      </ul>
    </div>
  </div>

  <div class="card">
    <h2>1. Your stocks</h2>
    <div class="row">
      <input id="tickerInput" type="text" placeholder="e.g. HUIZ, AAPL" autocomplete="off">
      <button class="btn-primary" onclick="addTicker()">Add</button>
    </div>
    <div id="chips" class="chips"></div>
    <div class="price-preview" id="pricePreview"></div>
  </div>

  <div class="card">
    <h2>2. Alert threshold</h2>
    <div class="row" style="align-items:center">
      <input id="threshold" type="number" step="0.5" min="1" max="100">
      <span style="color:var(--muted);font-size:14px">&nbsp;%</span>
    </div>
    <div class="hint">Alert when a stock moves at least this much from its previous close.</div>
  </div>

  <div class="card">
    <h2>3. Price source (data provider)</h2>
    <div style="margin-bottom:12px">
      <label>Provider</label>
      <select id="provider" onchange="updateProviderUI()">
        <option value="twelvedata">Twelve Data — real-time (recommended)</option>
        <option value="finnhub">Finnhub — real-time</option>
        <option value="yahoo">Yahoo Finance — ~15 min delayed, no key</option>
      </select>
    </div>
    <div style="margin-bottom:12px" id="apikeyRow">
      <label>Free API key (Twelve Data / Finnhub)</label>
      <input id="apikey" class="secret" type="text" placeholder="paste your free API key">
      <div class="hint">Get a free key: Twelve Data → twelvedata.com, Finnhub → finnhub.io.
      Yahoo needs no key. If the key is empty, it falls back to Yahoo.</div>
    </div>
  </div>

  <div class="card">
    <h2>4. Telegram notification</h2>
    <div style="margin-bottom:12px">
      <label>Bot Token</label>
      <input id="token" class="secret" type="text" placeholder="123456789:AAH...">
    </div>
    <div style="margin-bottom:12px">
      <label>Chat ID</label>
      <input id="chatid" type="text" placeholder="e.g. 123456789">
    </div>
    <button class="btn-ghost" onclick="testTelegram()">📲 Send test alert (shows live stats)</button>
    <div class="hint">This sends a real Telegram message with your first stock's live
    move vs its previous close. Great for checking everything works.</div>
  </div>

  <div class="card">
    <h2>5. Enable monitoring</h2>
    <div class="toggle-row">
      <span class="status" id="statusText">Loading...</span>
      <label class="switch">
        <input type="checkbox" id="enabledToggle">
        <span class="slider"></span>
      </label>
    </div>
  </div>

  <button class="btn-primary" style="width:100%;padding:14px" onclick="save()">💾 Save portfolio</button>
  <div class="msg" id="msg"></div>
</div>

<script>
let tickers = [];
let config = { threshold_pct: 5.0, enabled: false };

async function api(path, opts) {
  const r = await fetch(path, opts);
  return r.json();
}

async function load() {
  const data = await api('/api/config');
  config = data.config;
  tickers = data.config.tickers || [];
  document.getElementById('threshold').value = data.config.threshold_pct;
  document.getElementById('enabledToggle').checked = !!data.config.enabled;
  document.getElementById('provider').value = data.config.provider || 'twelvedata';
  document.getElementById('apikey').value = data.secrets.price_api_key || '';
  document.getElementById('token').value = data.secrets.telegram_bot_token || '';
  document.getElementById('chatid').value = data.secrets.telegram_chat_id || '';
  renderChips();
  updateStatus();
  updateProviderUI();
}

function updateProviderUI() {
  const p = document.getElementById('provider').value;
  document.getElementById('apikeyRow').style.display = (p === 'yahoo') ? 'none' : 'block';
}

function toggleGuide() {
  const guide = document.getElementById('guide');
  guide.style.display = (guide.style.display === 'none') ? 'block' : 'none';
}

function renderChips() {
  const el = document.getElementById('chips');
  el.innerHTML = '';
  tickers.forEach(t => {    const chip = document.createElement('span');
    chip.className = 'chip';
    chip.innerHTML = t + ' <button onclick="removeTicker(\\'' + t + '\\')">&times;</button>';
    el.appendChild(chip);
  });
}

function addTicker() {
  const input = document.getElementById('tickerInput');
  const t = input.value.trim().toUpperCase();
  if (!t) return;
  if (!tickers.includes(t)) {
    tickers.push(t);
    renderChips();
    checkPrice(t);
  }
  input.value = '';
}

function removeTicker(t) {
  tickers = tickers.filter(x => x !== t);
  renderChips();
}

async function checkPrice(symbol) {
  const el = document.getElementById('pricePreview');
  try {
    const d = await api('/api/price?symbol=' + symbol);
    if (d.error) { el.innerHTML = '<span>' + symbol + ': ' + d.error + '</span>'; return; }
    const cls = d.pct >= 0 ? 'up' : 'down';
    const arrow = d.pct >= 0 ? '▲' : '▼';
    el.innerHTML = '<span>' + symbol + ': $' + d.current.toFixed(2) +
      ' (prev $' + d.prev_close.toFixed(2) + ') <span class="' + cls + '">' + arrow + ' ' + d.pct + '%</span></span>';
  } catch(e) {
    el.innerHTML = '<span>Could not check price.</span>';
  }
}

function updateStatus() {
  const on = document.getElementById('enabledToggle').checked;
  const el = document.getElementById('statusText');
  el.textContent = on ? 'MONITORING ON' : 'Monitoring off';
  el.className = 'status ' + (on ? 'on' : 'off');
}

async function testTelegram() {
  const token = document.getElementById('token').value.trim();
  const chatid = document.getElementById('chatid').value.trim();
  if (!token || !chatid) {
    showMsg('❌ Enter your Telegram token and chat id first.', 'err');
    return;
  }
  showMsg('Sending test alert...', 'ok');
  const r = await api('/api/test', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ telegram_bot_token: token, telegram_chat_id: chatid })
  });
  if (r.ok) showMsg('✅ Test alert sent! Check your Telegram.', 'ok');
  else showMsg('❌ Failed: ' + (r.error || 'unknown'), 'err');
}

async function save() {
  const threshold = parseFloat(document.getElementById('threshold').value) || 5.0;
  const enabled = document.getElementById('enabledToggle').checked;
  const token = document.getElementById('token').value.trim();
  const chatid = document.getElementById('chatid').value.trim();
  const provider = document.getElementById('provider').value;
  const apikey = document.getElementById('apikey').value.trim();
  const r = await api('/api/save', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ tickers, threshold_pct: threshold, enabled, provider,
      telegram_bot_token: token, telegram_chat_id: chatid, price_api_key: apikey })
  });
  if (r.ok) {
    showMsg('✅ Saved! ' + tickers.length + ' ticker(s), threshold ' + threshold + '%.', 'ok');
  } else {
    showMsg('❌ Save failed.', 'err');
  }
}

function showMsg(text, type) {
  const el = document.getElementById('msg');
  el.textContent = text;
  el.className = 'msg ' + type;
  setTimeout(() => { el.className = 'msg'; }, 4000);
}

load();
</script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    url = f"http://127.0.0.1:{PORT}"
    print("PortfolioIsMoving setup running at", url)
    print("Close this window when done - monitoring runs in the cloud.")
    threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
