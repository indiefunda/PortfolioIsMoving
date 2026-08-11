# PortfolioIsMoving — Technical Reference

This document is the authoritative technical reference for the PortfolioIsMoving
system. It is written for AI assistants, maintainers, and engineers who need to
understand the complete architecture, data flow, and operational behavior of the
application.

---

## 1. Purpose

A free, self-hosted stock-movement alerting system. It monitors a user-selected
portfolio of US-listed stocks during US market hours and sends a Telegram push
notification when any stock moves more than a configurable threshold (default 5%)
from its previous trading day's close.

**Design goals:**
- 100% free (no paid services)
- Zero developer knowledge required to operate (non-developer friendly)
- 24/7 monitoring without keeping a personal computer on (via GitHub Actions)
- Per-provider API quota tracking with daily reset
- Runs on Windows via a single `start.bat` launcher

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│  LOCAL (Windows, user's machine)                            │
│                                                             │
│  start.bat → app.py (local web server, port 8000)           │
│              │                                              │
│              ├── config_local.json   (tickers, threshold,   │
│              │                       provider, enabled)     │
│              ├── secrets_local.json  (Telegram token/chat,  │
│              │                       price API key)  [git-ignored]
│              └── state.json          (daily alerts, daily   │
│                                       usage per provider)   │
│                                                             │
│  The app is a CONFIG + HEALTH PANEL. It is not the monitor. │
└─────────────────────────────────────────────────────────────┘
                        │  (config committed to repo)
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  CLOUD (GitHub Actions, free)                               │
│                                                             │
│  .github/workflows/monitor.yml  (cron every 10 min,         │
│                                   Mon-Fri 13-21 UTC)        │
│              │                                              │
│              ▼                                              │
│  monitor.py  → fetches prices from a provider               │
│              → compares to previous close                   │
│              → sends Telegram alert if > threshold          │
│              → updates state.json                           │
│              → commits state.json back to repo (anti-spam)  │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Data Flow

### 3.1 Price Fetching
`monitor.py` provides `get_prices(symbols, provider, api_key)` which dispatches
to one of three providers:

| Provider | Endpoint | Real-time? | Free tier limit | Prev close source |
|----------|----------|-----------|-----------------|-------------------|
| **Finnhub** (default) | `/api/v1/quote?symbol=X` | ✅ | 60 calls/min, no daily cap | Included in response (`pc`) |
| **Twelve Data** | `/api/price?symbol=X` | ✅ | 8 credits/min, 800/day | Fetched separately from Yahoo |
| **Yahoo Finance** | `/v8/finance/chart/X` | ❌ ~15 min delay | Unlimited, no key | Included in response |

**Provider selection logic** (`get_prices`):
- `provider == "twelvedata" and api_key` → `_fetch_twelvedata`
- `provider == "finnhub" and api_key` → `_fetch_finnhub`
- otherwise → `_fetch_yahoo` (automatic fallback, no key needed)

### 3.2 Alert Logic (`monitor.py:main`)
1. Load config; skip if not `enabled`.
2. Load Telegram credentials (env vars first, then secrets file).
3. **Market-hours gate**: skip unless Mon-Fri 09:25–16:05 ET.
4. Load `state.json`; reset `alerted` + `daily_usage` if the date changed.
5. Fetch prices.
6. For each ticker: compute `pct = (current - prev_close) / prev_close * 100`.
7. If `abs(pct) >= threshold` and ticker not in `alerted`, send Telegram alert
   and add to `alerted`.
8. Save `state.json`.

### 3.3 Anti-Spam (once per day)
`state.json` tracks the date and the list of tickers already alerted. The GitHub
Actions workflow **commits `state.json` back to the repo** after each run so the
"already alerted" list persists across runs. Without this, each run would start
fresh and a stock could alert every 10 minutes.

---

## 4. Configuration Files

### `config_local.json` (committed to repo)
```json
{
  "tickers": ["HUIZ", "YB", "LX"],
  "threshold_pct": 5.0,
  "enabled": false,
  "provider": "finnhub"
}
```
- `tickers`: array of stock symbols (uppercase).
- `threshold_pct`: alert when a stock moves at least this % from previous close.
- `enabled`: master on/off for the cloud monitor.
- `provider`: `finnhub` | `twelvedata` | `yahoo`.

### `secrets_local.json` (git-ignored — never commit)
```json
{
  "telegram_bot_token": "...",
  "telegram_chat_id": "...",
  "price_api_key": "..."
}
```
Contains the Telegram bot token, chat id, and the price-provider API key. In the
cloud, these come from GitHub Actions **secrets** (env vars), not this file.

### `state.json` (runtime, committed back by the cloud)
```json
{
  "date": "2026-08-11",
  "alerted": ["HUIZ"],
  "daily_usage": { "twelvedata": 41 }
}
```
- `date`: current trading day (used to reset daily state).
- `alerted`: tickers already alerted today (anti-spam).
- `daily_usage`: per-provider daily API call counter. Only Twelve Data has a real
  daily cap (800), so only it is tracked. Finnhub/Yahoo have no daily cap.

---

## 5. API Quota Tracking

Each provider has its own quota. The app tracks usage two ways:

1. **Per-minute** — captured free from response headers:
   - Finnhub: `X-Ratelimit-Remaining` / `X-Ratelimit-Limit`
   - Twelve Data: `api-credits-used` / `api-credits-left`
2. **Per-day** — Twelve Data exposes a real usage endpoint:
   `/api_usage` returns `current_usage`, `plan_limit`, `daily_usage`,
   `plan_daily_limit`. This reflects **all** usage for the API key across
   sessions. Finnhub has no daily cap and no public usage endpoint.

| Provider | Per-minute | Per-day | How daily is tracked |
|----------|-----------|---------|----------------------|
| Finnhub  | 60 | no cap (unlimited) | not tracked |
| Twelve Data | 8 | 800 | provider `/api_usage` |
| Yahoo | unlimited | unlimited | not tracked |

Daily usage resets each day at midnight (Twelve Data resets at midnight UTC).

---

## 6. GitHub Actions Workflow

`.github/workflows/monitor.yml`:
- **Schedule**: cron `*/10 13-21 * * 1-5` (every 10 min, hours 13-21 UTC, Mon-Fri).
  This runs wider than actual market hours (09:30–16:00 ET) to be robust across
  DST; `monitor.py` double-checks exact market hours.
- **Permissions**: `contents: write` — required to commit `state.json` back.
- **Secrets** (set in repo → Settings → Secrets and variables → Actions):
  - `TELEGRAM_BOT_TOKEN`
  - `TELEGRAM_CHAT_ID`
  - `PRICE_API_KEY` (optional; falls back to Yahoo if absent)
- **Steps**: checkout → setup python → pip install → run monitor.py → commit
  `state.json` back (for anti-spam persistence).

---

## 7. Local Web App (`app.py`)

A single-file Python HTTP server (stdlib `http.server`) serving an embedded HTML
UI at `http://localhost:8000`. It acts as:

1. **Config tool** — add/remove tickers, set threshold, choose provider, enter
   API key + Telegram credentials, enable/disable monitoring.
2. **Health panel** — `GET /api/health` validates the API key, fetches a live
   price, and reports per-minute/day usage, Telegram status, stock count, and
   monitoring state in one call.

### API Endpoints
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Serves the HTML UI |
| `/api/config` | GET | Returns config + secrets |
| `/api/price?symbol=X` | GET | Fetches a live price |
| `/api/health` | GET | Full health check |
| `/api/usage?provider=X&refresh=1` | GET | Usage gauges (optionally fetch a price) |
| `/api/save` | POST | Saves config + secrets |
| `/api/test` | POST | Sends a test Telegram alert with live stats |

---

## 8. Files

| File | Purpose |
|------|---------|
| `app.py` | Local config + health panel (embedded HTML UI, HTTP server) |
| `monitor.py` | Core monitor (price fetch, alert logic, state) |
| `start.bat` | Windows launcher (installs deps, opens app) |
| `config_local.json` | User portfolio config (committed) |
| `secrets_local.json` | Secrets (git-ignored) |
| `state.json` | Runtime state (committed back by cloud) |
| `.github/workflows/monitor.yml` | Free 24/7 cloud scheduler |
| `requirements.txt` | Dependencies: `requests`, `pytz` |
| `README.md` | Noob user guide |
| `README-DEVELOPER.md` | Developer guide |
| `README-TECHNICAL.md` | This document |

---

## 9. Dependencies
- `requests` — HTTP calls to providers + Telegram.
- `pytz` — US/Eastern timezone handling for market-hours gate.
- Python standard library — `http.server`, `json`, `webbrowser`, `threading`.

---

## 10. Security Notes
- **Never commit `secrets_local.json`** — it holds the Telegram token and API key.
- API keys and Telegram credentials are stored in GitHub Actions secrets for the
  cloud runner (env vars), not in the repo.
- `config_local.json` and `state.json` are safe to commit (no secrets).

---

## 11. Known Limitations
- Free price data may be delayed (Yahoo ~15 min) or rate-limited (Twelve Data 800/day).
- GitHub Actions free tier: public repos get unlimited minutes; private repos have
  a 2,000 min/month allowance.
- The cloud runner needs `contents: write` permission to persist anti-spam state.
