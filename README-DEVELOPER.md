# PortfolioIsMoving — Developer Guide

For developers who want to run, extend, or package this project. If you're not a
developer, read `README.md` instead.

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Create your local config (tickers, threshold, provider, Telegram, API key)
python app.py
# Opens http://localhost:8000 in your browser

# 3. Run one monitor check manually
python monitor.py
```

---

## Project Structure

```
PortfolioIsMoving/
├── app.py                  # Local config + health panel (HTTP server + embedded UI)
├── monitor.py              # Core monitor (price fetch, alert logic, state)
├── start.bat               # Windows launcher for non-developers
├── build_exe.bat           # Builds a single .exe (via PyInstaller)
├── config_local.json       # User portfolio config (committed)
├── secrets_local.json      # Secrets — git-ignored, never commit
├── state.json              # Runtime state (alerted list, daily usage)
├── requirements.txt        # requests, pytz
├── .github/workflows/monitor.yml  # GitHub Actions 24/7 scheduler
├── README.md               # Noob guide
├── README-DEVELOPER.md     # This file
└── README-TECHNICAL.md     # Full technical reference / AI-readable
```

---

## Running Locally

### 1. Set up config
```bash
python app.py
```
This starts a web server at `http://localhost:8000`. Use the UI to:
- Add/remove tickers
- Set the threshold (%)
- Choose a provider (Finnhub / Twelve Data / Yahoo)
- Enter your API key
- Enter your Telegram bot token + chat id
- Enable/disable monitoring

The UI writes `config_local.json` and `secrets_local.json`.

### 2. Run a single monitor check
```bash
python monitor.py
```
This runs the alert check once. It skips if:
- Monitoring is disabled (`enabled: false`)
- Telegram credentials are missing
- The market is closed (Mon-Fri 09:25–16:05 ET)

### 3. Test Telegram
Use the "Send test alert" button in the app, or call:
```bash
python -c "import monitor; print(monitor.send_telegram('TOKEN','CHAT_ID','test'))"
```

---

## Providers

| Provider | Real-time | Free limit | Notes |
|----------|-----------|-----------|-------|
| **Finnhub** (default) | ✅ | 60 calls/min, no daily cap | `/quote` returns current + prev close |
| **Twelve Data** | ✅ | 8 credits/min, 800/day | `/price` for live, prev close from Yahoo |
| **Yahoo** | ❌ ~15 min delay | Unlimited | Automatic fallback, no key |

The provider is set in `config_local.json` (`"provider": "finnhub"`). The API key
goes in `secrets_local.json` (`price_api_key`) or as a `PRICE_API_KEY` env var.

---

## Building the .exe (optional)

If you want to give non-developers a single file (no Python install):

```bash
pip install pyinstaller
build_exe.bat
```

The output is `dist/PortfolioIsMoving.exe`. It runs the same `app.py` web panel.

---

## Testing

There is no formal test suite. Manual verification:
1. `python app.py` → ensure the page loads.
2. Add a ticker → verify a live price appears.
3. Run "Health check" → verify API key + price + usage display.
4. `python monitor.py` → verify it runs (or skips gracefully outside market hours).

To verify price fetching without the server:
```bash
python -c "import monitor; print(monitor.get_prices(['HUIZ'], provider='finnhub', api_key='YOUR_KEY'))"
```

---

## GitHub Actions (24/7 cloud)

`.github/workflows/monitor.yml` runs `monitor.py` every 10 min during market hours.

**Required secrets** (repo → Settings → Secrets and variables → Actions):
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `PRICE_API_KEY` (optional — falls back to Yahoo)

**Important**: the workflow has `contents: write` permission so it can commit
`state.json` back. This preserves the anti-spam "already alerted today" list
across runs. Without it, a stock could alert every 10 minutes.

---

## Configuration Reference

### `config_local.json`
```json
{
  "tickers": ["HUIZ", "YB", "LX"],
  "threshold_pct": 5.0,
  "enabled": false,
  "provider": "finnhub"
}
```

### `secrets_local.json` (git-ignored)
```json
{
  "telegram_bot_token": "...",
  "telegram_chat_id": "...",
  "price_api_key": "..."
}
```

### `state.json`
```json
{
  "date": "2026-08-11",
  "alerted": ["HUIZ"],
  "daily_usage": { "twelvedata": 41 }
}
```

---

## Contributing / Extending

- **Add a provider**: add a `_fetch_<name>` function in `monitor.py`, add the
  endpoint constant, add the provider to `get_prices()`, and add it to the
  provider dropdown in `app.py`.
- **Change the check interval**: edit the cron in `.github/workflows/monitor.yml`.
- **Change the threshold logic**: edit `monitor.py:main()`.
- **UI**: the entire UI is an embedded HTML string in `app.py` (`HTML = """..."""`).

---

## Troubleshooting

| Symptom | Cause / Fix |
|---------|-------------|
| "No config_local.json found" | Run `python app.py` first to create it. |
| "Telegram credentials missing" | Set `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID` secrets (cloud) or enter in the app. |
| Price fetch fails | Check the API key is valid for the selected provider. |
| Alerts every 10 min (not once/day) | `state.json` isn't being persisted — check the workflow has `contents: write` and the "Save state" step. |
| Port 8000 in use | Another instance is running. Close it or change `PORT` in `app.py`. |
