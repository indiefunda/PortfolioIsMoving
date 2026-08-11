# 📈 PortfolioIsMoving

A **100% free** stock movement alert system. It watches your portfolio during US
market hours and sends you a **Telegram push notification** whenever a stock moves
more than a threshold you choose (default **5%**) from the previous trading day's
close.

Checks every **10 minutes**, runs **24/7 in the cloud** via GitHub Actions (no need
to keep your computer on), and costs nothing.

---

## How it works

```
┌─────────┐   saves    ┌──────────────┐
│  gui.py │ ─────────▶ │ config_local │
│ (desktop│            │    .json     │
│  window)│            └──────┬───────┘
└─────────┘                    │ (tickers, threshold, enabled)
                               ▼
┌─────────────────────────────────────────────┐
│  GitHub Actions (free cloud scheduler)      │
│  runs every 10 min, Mon-Fri, market hours   │
│         │                                   │
│         ▼                                   │
│  monitor.py  ──▶ Yahoo Finance (free price) │
│         │                                   │
│         ▼                                   │
│  >5% move? ──▶ Telegram bot ──▶ your iPhone │
└─────────────────────────────────────────────┘
```

- **Price source:** Yahoo Finance (free, no API key, no account)
- **Alerts:** Telegram bot (free, push notifications)
- **Hosting:** GitHub Actions free tier (public repo = unlimited minutes)
- **Baseline:** previous trading day's close
- **Anti-spam:** each stock alerts only once per day

---

## What you need to do (one-time setup, ~5 minutes)

### 1. Create your Telegram bot (free)
1. Open **Telegram** on your phone.
2. Search for **@BotFather** (the official bot).
3. Send `/newbot`, pick a name, then a username (must end in `bot`, e.g. `my_stock_alert_bot`).
4. BotFather replies with a **token** that looks like:
   `123456789:AAH...` — **copy and save it.**
5. Now find your **chat id**:
   - Open your new bot in Telegram and press **Start** (send it any message).
   - Visit `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates` in a browser.
   - Look for `"chat":{"id":123456789,...}` — that number is your **chat id**.

### 2. Set your portfolio (on your computer)
Open a terminal in this folder and run:
```
python gui.py
```
- Type a ticker (e.g. `HUIZ`) and click **Add**.
- Set your threshold (default 5%).
- Tick **Enable monitoring**.
- Click **Save portfolio**.

This writes `config_local.json` (which is git-ignored, so it stays private).

### 3. Connect it to GitHub (so it runs 24/7 for free)
1. Push this repo to GitHub (see below).
2. Go to your repo on GitHub → **Settings → Secrets and variables → Actions**.
3. Add two **repository secrets**:
   - `TELEGRAM_BOT_TOKEN` = the token from step 1
   - `TELEGRAM_CHAT_ID` = the chat id from step 1
4. The workflow `Monitor Portfolio` is now scheduled. It runs every 10 min during
   US market hours, Mon–Fri.

> **Important:** your `config_local.json` (with tickers) must be in the repo for
> the cloud runner to read it. Since it's git-ignored locally, either:
> - commit a `config_local.json` with your tickers (no secrets in it), **or**
> - rename the sample to `config_local.json` and commit it.

### 4. Verify it works
- On GitHub, open the **Actions** tab → **Monitor Portfolio** → **Run workflow**
  (manual trigger) to test immediately.
- Check the run logs — you'll see each ticker and its % move.
- If a stock is past the threshold, you'll get a Telegram push.

---

## Files

| File | Purpose |
|------|---------|
| `gui.py` | Desktop app to add/remove tickers, set threshold, enable/disable |
| `monitor.py` | The core checker (prices + Telegram alert) |
| `config_local.json` | Your portfolio (tickers, threshold, enabled) — git-ignored |
| `.github/workflows/monitor.yml` | Free 24/7 cloud scheduler (every 10 min, market hours) |
| `requirements.txt` | Dependencies (`requests`, `pytz`) |

---

## Running locally (optional)

You don't need to run anything locally once it's on GitHub. But to test on your
own machine:
```
pip install -r requirements.txt
python gui.py          # set up and enable your portfolio
python monitor.py      # run one check now
```

---

## Notes & limitations

- **Free price data is ~15 min delayed.** For illiquid stocks moving over hours,
  that's plenty fast.
- **One alert per stock per day** — you won't be spammed every 10 minutes.
- **GitHub Actions free tier:** public repos get unlimited minutes. This repo is
  public by default, so it's fully free. (If you make it private, the 2,000
  free minutes/month still easily cover ~820 scheduled runs.)
- The workflow runs a few extra minutes around market open/close to be safe
  across daylight-saving changes; `monitor.py` itself only acts during
  actual market hours.
