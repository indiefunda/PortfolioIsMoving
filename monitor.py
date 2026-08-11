#!/usr/bin/env python3
"""
PortfolioIsMoving - free stock movement monitor.

Checks configured stocks against their previous trading day's close and sends
a Telegram alert when a stock moves more than the configured threshold.

Price source : Yahoo Finance (free, no API key)
Alerts      : Telegram bot (free)
"""

import json
import os
import sys
import time
from datetime import datetime, time as dtime

import pytz
import requests

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config_local.json")
STATE_FILE = os.path.join(BASE_DIR, "state.json")

# US Eastern timezone (NY market)
EASTERN = pytz.timezone("US/Eastern")

# Telegram API
TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"

# Yahoo Finance quote endpoint (free, unofficial)
YAHOO_QUOTE = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=5d"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    )
}


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


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


# ---------------------------------------------------------------------------
# Price fetching (Yahoo Finance)
# ---------------------------------------------------------------------------
def get_price_and_prev_close(symbol):
    """
    Fetch current price and previous trading day close for a symbol.
    Returns (current_price, prev_close) or (None, None) on failure.
    """
    url = YAHOO_QUOTE.format(symbol=symbol)
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        result = data["chart"]["result"][0]
        meta = result["meta"]
        closes = result.get("indicators", {}).get("quote", [{}])[0].get("close", [])

        current = meta.get("regularMarketPrice")
        if current is None and closes:
            # Fall back to last close in the series
            current = [c for c in closes if c is not None][-1]

        # Previous close: use the second-to-last non-None close, else meta
        prev_close = None
        valid = [c for c in closes if c is not None]
        if len(valid) >= 2:
            prev_close = valid[-2]
        if prev_close is None:
            prev_close = meta.get("chartPreviousClose") or meta.get("previousClose")

        return current, prev_close
    except Exception as exc:
        print(f"  [error] {symbol}: {exc}", file=sys.stderr)
        return None, None


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
        print("No config_local.json found. Run gui.py first to set up your portfolio.")
        return

    enabled = config.get("enabled", False)
    if not enabled:
        print("Monitoring is disabled (enabled=false). Enable it in gui.py.")
        return

    tickers = config.get("tickers", [])
    threshold = float(config.get("threshold_pct", 5.0))
    token = os.environ.get("TELEGRAM_BOT_TOKEN") or config.get("telegram_bot_token", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID") or config.get("telegram_chat_id", "")

    if not tickers:
        print("No tickers configured. Add some in gui.py.")
        return
    if not token or not chat_id:
        print("Telegram credentials missing. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID.")
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
        state = {"date": today, "alerted": []}

    print(f"[{now_et.strftime('%Y-%m-%d %H:%M %Z')}] Checking {len(tickers)} ticker(s)...")

    for symbol in tickers:
        symbol = symbol.strip().upper()
        if not symbol:
            continue

        current, prev_close = get_price_and_prev_close(symbol)
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
