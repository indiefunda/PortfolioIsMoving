#!/usr/bin/env python3
"""
PortfolioIsMoving - free stock movement monitor.

Checks configured stocks against their previous trading day's close and sends
a Telegram alert when a stock moves more than the configured threshold.

Price sources (choose in app.py):
  - Finnhub (default):      real-time US stocks, 60 calls/min free, gets prev close
  - Twelve Data:            real-time US stocks, 8 credits/min free
  - Yahoo Finance:          ~15 min delayed, unlimited, no key (automatic fallback)
Alerts      : Telegram bot (free)
"""

import json
import os
import sys
from datetime import datetime, time as dtime

import pytz
import requests

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config_local.json")
SECRETS_FILE = os.path.join(BASE_DIR, "secrets_local.json")
STATE_FILE = os.path.join(BASE_DIR, "state.json")

# US Eastern timezone (NY market)
EASTERN = pytz.timezone("US/Eastern")

# Telegram API
TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"

# ---- Price provider endpoints ----
# Twelve Data (default): real-time US stocks. /price = live price (1 credit/symbol).
TWELVE_PRICE = "https://api.twelvedata.com/price?symbol={symbols}&apikey={key}"
# Finnhub: real-time US stocks, free tier = 60/min
FINNHUB_QUOTE = "https://finnhub.io/api/v1/quote?symbol={symbol}&token={key}"
# Yahoo Finance (fallback + prev close): ~15 min delayed, unlimited, no key
YAHOO_QUOTE = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=5d"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    )
}

# Default provider if none configured. "finnhub" = real-time, 60 calls/min,
# returns current + prev close in one call (best fit for this app).
DEFAULT_PROVIDER = "finnhub"


# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------
def load_config():
    """Load config_local.json. Returns dict or None if missing."""
    if not os.path.exists(CONFIG_FILE):
        return None
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_state():
    """Load state.json (which tickers already alerted today)."""
    if not os.path.exists(STATE_FILE):
        return {"date": None, "alerted": []}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"date": None, "alerted": []}


def load_secrets():
    """Load Telegram credentials from secrets_local.json (local testing only)."""
    if not os.path.exists(SECRETS_FILE):
        return {}
    try:
        with open(SECRETS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


# ---------------------------------------------------------------------------
# Price fetching (multiple free providers)
# ---------------------------------------------------------------------------
# Twelve Data free tier: 8 API credits/min, 800/day.
#   /price  = 1 credit/symbol (live price only)  <- cheap, use for live price
#   /quote  = 2 credits/symbol (price + prev close)
# Strategy: get LIVE price from Twelve Data /price (cheap), and PREVIOUS CLOSE
# from Yahoo Finance (free, unlimited, great coverage of illiquid tickers).
TWELVE_BATCH_SIZE = 8  # /price is 1 credit/symbol; 8 fits the 8/min limit

# Latest Twelve Data usage info captured from response headers (free, no extra call).
# Structure: {"used_min": int, "left_min": int, "daily_used": int, "daily_limit": int}
last_usage = {}


def get_last_usage():
    """Return the latest usage info captured from price-call headers."""
    return last_usage


def _fetch_twelvedata(symbols, api_key):
    """
    Twelve Data - real-time live price (via /price, 1 credit/symbol).
    Previous close comes from Yahoo (free). Returns {symbol: (current, prev_close)}.
    """
    global last_usage
    result = {}
    # Step 1: live prices from Twelve Data /price (cheap, real-time)
    live = {}
    used_min = None
    left_min = None
    for i in range(0, len(symbols), TWELVE_BATCH_SIZE):
        chunk = symbols[i:i + TWELVE_BATCH_SIZE]
        try:
            resp = requests.get(
                TWELVE_PRICE.format(symbols=",".join(chunk), key=api_key),
                timeout=15,
            )
            resp.raise_for_status()
            # Free usage info from response headers (no extra API call).
            try:
                used_min = int(resp.headers.get("api-credits-used", used_min or 0))
                left_min = int(resp.headers.get("api-credits-left", left_min or 0))
            except (ValueError, TypeError):
                pass
            data = resp.json()
            # Batch returns {symbol: {"price": "..."}}; single returns {"price": "..."}
            if isinstance(data, dict) and "price" in data:
                live[chunk[0].upper()] = float(data["price"])
            else:
                for sym, q in data.items():
                    if isinstance(q, dict) and "price" in q:
                        live[sym.upper()] = float(q["price"])
        except Exception as exc:
            print(f"  [error] twelvedata {chunk}: {exc}", file=sys.stderr)

    if not live:
        return result

    # Step 2: previous close from Yahoo (free, unlimited, good illiquid coverage)
    prev = _fetch_yahoo(list(live.keys()))

    # Combine: live price (Twelve) + prev close (Yahoo)
    for sym, cur in live.items():
        if sym in prev:
            result[sym] = (cur, prev[sym][1])
        else:
            result[sym] = (cur, None)

    # Set Twelve Data usage AFTER the Yahoo call so it isn't overwritten.
    if used_min is not None and left_min is not None:
        last_usage = {
            "used_min": used_min,
            "left_min": left_min,
            "limit_min": used_min + left_min,
            "delay": "real-time",
        }
    return result


def _fetch_finnhub(symbols, api_key):
    """Finnhub - real-time, one call per symbol. Returns {symbol: (current, prev_close)}."""
    global last_usage
    result = {}
    remaining = None
    limit = None
    for sym in symbols:
        try:
            resp = requests.get(
                FINNHUB_QUOTE.format(symbol=sym, key=api_key), timeout=15
            )
            resp.raise_for_status()
            # Capture Finnhub rate-limit info (free, from response headers).
            try:
                remaining = int(resp.headers.get("X-Ratelimit-Remaining", remaining or 0))
                limit = int(resp.headers.get("X-Ratelimit-Limit", limit or 0))
            except (ValueError, TypeError):
                pass
            q = resp.json()
            current = q.get("c")
            prev_close = q.get("pc")
            if current is None or prev_close is None or current == 0:
                continue
            result[sym.upper()] = (float(current), float(prev_close))
        except Exception as exc:
            print(f"  [error] finnhub {sym}: {exc}", file=sys.stderr)

    if limit and remaining is not None:
        last_usage = {
            "used_min": limit - remaining,
            "left_min": remaining,
            "limit_min": limit,
            "delay": "real-time",
        }
    return result


def _fetch_yahoo(symbols):
    """Yahoo Finance - ~15 min delayed, unlimited, no key. Returns {symbol: (current, prev_close)}."""
    global last_usage
    result = {}
    for sym in symbols:
        try:
            resp = requests.get(YAHOO_QUOTE.format(symbol=sym), headers=HEADERS, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            meta = data["chart"]["result"][0]["meta"]
            closes = data["chart"]["result"][0].get("indicators", {}).get("quote", [{}])[0].get("close", [])
            current = meta.get("regularMarketPrice")
            if current is None and closes:
                current = [c for c in closes if c is not None][-1]
            prev_close = None
            valid = [c for c in closes if c is not None]
            if len(valid) >= 2:
                prev_close = valid[-2]
            if prev_close is None:
                prev_close = meta.get("chartPreviousClose") or meta.get("previousClose")
            if current is None or prev_close is None:
                continue
            result[sym.upper()] = (float(current), float(prev_close))
        except Exception as exc:
            print(f"  [error] yahoo {sym}: {exc}", file=sys.stderr)

    # Yahoo has no rate limit; report its documented delay.
    last_usage = {
        "used_min": None,
        "left_min": None,
        "limit_min": None,
        "delay": "~15 min delayed",
    }
    return result


def get_prices(symbols, provider=DEFAULT_PROVIDER, api_key=""):
    """
    Fetch current price and previous-close for a list of symbols.
    Returns {symbol: (current, prev_close)}. Falls back gracefully.
    """
    symbols = [s.strip().upper() for s in symbols if s.strip()]
    if not symbols:
        return {}

    if provider == "twelvedata" and api_key:
        return _fetch_twelvedata(symbols, api_key)
    if provider == "finnhub" and api_key:
        return _fetch_finnhub(symbols, api_key)
    # Default / fallback: Yahoo (no key needed)
    return _fetch_yahoo(symbols)


# ---------------------------------------------------------------------------
# Telegram alerts
# ---------------------------------------------------------------------------
def send_telegram(token, chat_id, message):
    """Send a message via Telegram bot. Returns True on success."""
    url = TELEGRAM_API.format(token=token)
    payload = {"chat_id": chat_id, "text": message}
    try:
        resp = requests.post(url, data=payload, timeout=15)
        resp.raise_for_status()
        return True
    except Exception as exc:
        print(f"  [error] Telegram send failed: {exc}", file=sys.stderr)
        return False


def format_alert(symbol, current, prev_close, pct, threshold):
    direction = "🚨 UP" if pct > 0 else "📉 DOWN"
    arrow = "▲" if pct > 0 else "▼"
    return (
        f"{direction} {symbol}\n"
        f"{arrow} {abs(pct):.1f}%  (threshold {threshold}%)\n"
        f"Price: ${current:.2f}  |  Prev close: ${prev_close:.2f}"
    )


# ---------------------------------------------------------------------------
# Market-hours gating
# ---------------------------------------------------------------------------
def is_market_hours(now_et):
    """
    True if now is during US market hours (Mon-Fri 9:30-16:00 ET).
    We allow a little slack: 9:25 open / 16:05 close.
    """
    if now_et.weekday() >= 5:  # Sat/Sun
        return False
    open_t = dtime(9, 25)
    close_t = dtime(16, 5)
    return open_t <= now_et.time() <= close_t


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    config = load_config()
    if not config:
        print("No config_local.json found. Run app.py to set up your portfolio.")
        return

    enabled = config.get("enabled", False)
    if not enabled:
        print("Monitoring is disabled (enabled=false). Enable it in app.py.")
        return

    tickers = config.get("tickers", [])
    threshold = float(config.get("threshold_pct", 5.0))
    provider = config.get("provider", DEFAULT_PROVIDER)
    secrets = load_secrets()
    token = os.environ.get("TELEGRAM_BOT_TOKEN") or secrets.get("telegram_bot_token", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID") or secrets.get("telegram_chat_id", "")
    api_key = os.environ.get("PRICE_API_KEY") or secrets.get("price_api_key", "")

    if not tickers:
        print("No tickers configured. Run app.py to add some.")
        return
    if not token or not chat_id:
        print("Telegram credentials missing. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID "
              "(cloud) or run app.py to enter them locally.")
        return

    # Market-hours gate (skip when market closed)
    now_et = datetime.now(EASTERN)
    if not is_market_hours(now_et):
        print(f"Skipping: outside market hours ({now_et.strftime('%a %H:%M %Z')}).")
        return

    # Reset daily alert state if the date changed
    state = load_state()
    today = now_et.strftime("%Y-%m-%d")
    if state.get("date") != today:
        state = {"date": today, "alerted": [], "daily_usage": 0}

    print(f"[{now_et.strftime('%Y-%m-%d %H:%M %Z')}] Checking {len(tickers)} ticker(s) "
          f"via {provider}...")

    prices = get_prices(tickers, provider=provider, api_key=api_key)

    # Track daily usage: each keyed provider makes 1 call per symbol checked.
    if api_key and provider in ("finnhub", "twelvedata"):
        state["daily_usage"] = int(state.get("daily_usage", 0)) + len(prices)

    for symbol in tickers:
        symbol = symbol.strip().upper()
        if not symbol:
            continue

        pair = prices.get(symbol)
        if pair is None:
            print(f"  - {symbol}: no data")
            continue
        current, prev_close = pair

        if current is None or prev_close is None or prev_close == 0:
            print(f"  - {symbol}: no data")
            continue

        pct = ((current - prev_close) / prev_close) * 100.0
        print(f"  - {symbol}: ${current:.2f} vs ${prev_close:.2f} = {pct:+.2f}%")

        if abs(pct) >= threshold:
            if symbol in state["alerted"]:
                print(f"    already alerted, skipping.")
                continue
            msg = format_alert(symbol, current, prev_close, pct, threshold)
            if send_telegram(token, chat_id, msg):
                state["alerted"].append(symbol)
                print(f"    ALERT sent to Telegram.")
            else:
                print(f"    ALERT failed to send.")
        else:
            print(f"    within threshold, no alert.")

    save_state(state)


if __name__ == "__main__":
    main()
