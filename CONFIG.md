# Configuration Reference

This document explains every option in `config_local.json` and what it does.
This file is what controls the app and the cloud monitor.

---

## Where is the config file?

`config_local.json` lives in the main folder. The app (`start.bat`) reads and
writes it. It's also committed to GitHub so the cloud monitor knows your settings.

> ⚠️ **Important:** the file is called `config_local` but it IS shared with the
> cloud. After you change it in the app, you must **upload the new `config_local.json`
> to your GitHub copy** for the cloud monitor to use it.

---

## The options

Here's an example with every option:

```json
{
  "tickers": ["HUIZ", "YB", "LX"],
  "threshold_pct": 5.0,
  "enabled": true,
  "provider": "finnhub"
}
```

### `tickers` (required)
Your list of stock symbols (the short codes).

```json
"tickers": ["HUIZ", "YB", "LX"]
```

- Each ticker is the short code for a stock (e.g. `AAPL` = Apple, `HUIZ` = Huize).
- Use **uppercase** letters.
- Add as many as you like (up to ~10-12 is comfortable for the free tiers).
- To find a ticker, search "stock ticker for <company name>".

### `threshold_pct` (required)
How big a move triggers an alert.

```json
"threshold_pct": 5.0
```

- The alert fires when a stock moves **at least this %** from the previous day's close.
- `5.0` = alert when it moves 5% or more.
- Set higher (e.g. `10.0`) for less sensitive, or lower (e.g. `2.0`) for more sensitive.

### `enabled` (required)
The master on/off switch for the monitor. **Defaults to ON (`true`).**

```json
"enabled": true
```

- `true` = monitoring is ON (the cloud monitor checks during US market hours).
- `false` = monitoring is OFF (the cloud monitor skips runs).
- Turn it off in the app by switching **"Enable monitoring"** to OFF and clicking Save.

> 💡 This is the most common reason the GitHub monitor says "disabled" — you
> haven't switched it ON yet.

### `provider` (required)
Which price provider to use.

```json
"provider": "finnhub"
```

| Value | Provider | Real-time? | Free limit |
|-------|----------|-----------|-----------|
| `finnhub` | Finnhub | ✅ Yes | 60 calls/min, no daily cap |
| `twelvedata` | Twelve Data | ✅ Yes | 8 credits/min, 800/day |
| `yahoo` | Yahoo Finance | ❌ ~15 min delayed | Unlimited, no key |

- **`finnhub`** (recommended) — real-time, generous limits, no daily cap.
- **`twelvedata`** — real-time, but has a daily cap (800/day).
- **`yahoo`** — no key needed, but ~15 min delayed.

---

## How the app and cloud use this

| Setting | Used by the app (local) | Used by the cloud monitor |
|---------|------------------------|---------------------------|
| `tickers` | ✅ shows your stocks | ✅ checks these stocks |
| `threshold_pct` | ✅ sets the % | ✅ decides when to alert |
| `enabled` | ✅ the on/off switch | ✅ skips if off |
| `provider` | ✅ picks the provider | ✅ picks the provider + API key |

---

## Related files

| File | Purpose | Git? |
|------|---------|------|
| `config_local.json` | Your settings (this file) | ✅ committed |
| `secrets_local.json` | Your API keys + Telegram (private) | ❌ git-ignored |
| `state.json` | Runtime: which stocks alerted today | ✅ committed back by cloud |

---

## Changing your settings

1. Run `start.bat` → change settings in the app → click **Save**.
2. The app writes the new `config_local.json`.
3. **Upload** the new `config_local.json` to your GitHub copy (Add file → Upload files → Commit).
4. The cloud monitor uses the new settings on its next run.

> ⚠️ Never edit `config_local.json` by hand unless you know JSON. Use the app.
