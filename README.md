# 📈 PortfolioIsMoving

A **100% free** app that watches your stocks during US market hours and sends you a
**Telegram message on your phone** whenever one of your stocks moves more than a
threshold you choose (default **5%**) from the previous trading day's close.

- Checks every **10 minutes**
- Runs **24/7 in the cloud** — your computer can be **off** after setup
- Costs **nothing**
- No "developer" skills needed — just follow this guide

---

## How it works (in plain English)

1. You run a tiny **setup screen** on your computer **once**.
2. You type your stock tickers, set a threshold, enter your Telegram info, click **Enable**.
3. That's it. A free **cloud service (GitHub Actions)** watches your stocks every 10
   minutes during US market hours and texts you on Telegram when a stock moves.

Your computer only needs to be on for **step 1**. After that it can be turned off.

---

## First-time setup (do this once, ~10 minutes)

### Step 1 — Install Python (only if you don't have it)

1. Go to **https://www.python.org/downloads/**
2. Click the big yellow **"Download Python"** button.
3. Open the downloaded file.
4. **IMPORTANT:** tick the box that says **"Add Python to PATH"** (bottom of the window).
5. Click **Install Now** and wait for it to finish.

> If you're not sure whether you already have Python, just try Step 2 — if it opens
> the setup screen, you're fine.

### Step 2 — Open the setup screen

**Double-click `start.bat`** (in this folder).

A small black window will open. It checks for Python, installs two small libraries
(only the first time), and then opens the setup page in your browser. Just follow
the messages on screen.

> If nothing opens in your browser, type this into the browser's address bar:
> **http://localhost:8000**

### Step 3 — Create your Telegram bot (free, 2 minutes)

This is how alerts reach your phone.

1. On your phone, open **Telegram**.
2. Search for **@BotFather** (the official bot with a blue checkmark).
3. Send it the message: **`/newbot`**
4. It asks for a **name** — type anything, e.g. `My Stock Alerts`.
5. It asks for a **username** — must end in `bot`, e.g. `mystockalerts_bot`.
6. BotFather replies with a **token** that looks like:
   `123456789:AAH...` — **copy it** and keep it somewhere.

Now get your **chat id**:
7. In Telegram, open **your new bot** and press **Start** (send it any message).
8. On your computer, open a browser and go to:
   `https://api.telegram.org/bot<PASTE_YOUR_TOKEN_HERE>/getUpdates`
   (replace `<PASTE_YOUR_TOKEN_HERE>` with your actual token)
9. You'll see some text. Look for `"chat":{"id":123456789` — that number is your **chat id**.

### Step 4 — Fill in the setup screen

On the setup page:

1. **Your stocks** — type a ticker (e.g. `HUIZ`, `AAPL`) and click **Add**. Add as many as you like.
   (A ticker is the short code for a stock. If unsure, search "stock ticker for <company name>".)
2. **Alert threshold** — leave at **5** (means "alert when it moves more than 5%").
3. **Telegram** — paste your **bot token** and **chat id** from Step 3.
   - Click **"Send test alert"** — you should get a Telegram message on your phone. If not, double-check the token and chat id.
4. **Enable monitoring** — switch it **ON**.
5. Click **💾 Save portfolio**.

**Done!** Your stocks are saved. You can close the black window and the browser tab.

---

## Step 5 — Connect to GitHub (so it runs 24/7 for free)

> This is the only slightly technical part. Do it once, carefully.

### A. Create a free GitHub account (if you don't have one)
1. Go to **https://github.com/** and click **Sign up**.
2. Pick a username, email, password. Confirm your email.

### B. Make your own copy of this project
1. Open this project's GitHub page (ask the person who gave you this for the link).
2. Click the **Fork** button (top-right). This makes a copy under **your** account.
3. Wait a few seconds — you now have your own copy.

### C. Tell GitHub your info (as "secrets")
1. On **your** copy's page, click **Settings** (top tab).
2. In the left menu, click **Secrets and variables** → **Actions**.
3. Click **New repository secret**.
4. Name: `TELEGRAM_BOT_TOKEN` → paste your bot token → **Add secret**.
5. Click **New repository secret** again.
6. Name: `TELEGRAM_CHAT_ID` → paste your chat id → **Add secret**.
7. **Optional but recommended:** if you use Twelve Data or Finnhub (real-time),
   add a third secret:
   - Name: `PRICE_API_KEY` → paste your free API key → **Add secret**.

> If you don't add `PRICE_API_KEY`, the monitor automatically falls back to
> Yahoo Finance (free, ~15 min delayed, no key needed).

### D. Make sure your stocks are in your copy
Your `config_local.json` file (with your tickers) needs to be in your GitHub copy.
The easiest way:
1. In your copy on GitHub, click **Add file** → **Upload files**.
2. Upload your `config_local.json` from this folder.
3. Click **Commit changes**.

> ⚠️ Do **NOT** upload `secrets_local.json` — that one has your private Telegram token.

### E. Turn on the monitor
1. In your copy, click the **Actions** tab.
2. If GitHub asks, click **"I understand my workflows, go ahead and enable them"**.
3. You'll see a workflow named **Monitor Portfolio**. Click it → **Run workflow** → **Run**.
4. Watch the log — it should check your stocks. You'll see each ticker and its % move.

That's it. From now on it runs automatically **every 10 minutes during US market hours, Mon–Fri**.

---

## When you want to change your stocks

1. Run the setup screen again (`start.bat`).
2. Change your tickers / threshold, click **Save**.
3. Re-upload the new `config_local.json` to your GitHub copy (Step D above).
4. That's it — the monitor uses the new list on its next run.

---

## FAQ

**Does my computer need to stay on?**
No. After setup, everything runs in the cloud. Turn your computer off.

**Is it really free?**
Yes. Telegram is free. GitHub Actions is free for public repos (this one is public).

**How fast is the alert?**
Prices are checked every 10 minutes. The delay depends on your **price source**:
- **Twelve Data** or **Finnhub** (free API key) → **real-time**, no delay.
- **Yahoo Finance** (no key, default fallback) → ~15 minutes delayed.

Either is plenty for stocks that move over hours.

**Will it work for illiquid / small / Chinese-listed stocks (like HUIZ, YB, LX)?**
Yes — this was tested. The app uses a **hybrid** approach:
- **Live price** comes from your chosen real-time provider (Twelve Data / Finnhub).
- **Previous close** comes from **Yahoo Finance** (free, unlimited, great coverage
  of small and foreign-listed stocks).

All of **HUIZ** (Huize), **YB** (Yuanbao), and **LX** (LexinFintech) returned real
prices in testing. These are US-listed (NASDAQ) stocks, so they're covered.

**How many stocks can I track for free?**
- Twelve Data free tier: **800 requests/day**, and the app uses **1 credit per stock**
  for the live price (the previous close is free via Yahoo).
- With checks every 10 minutes (~39/day), you can easily track **dozens of stocks**
  within the free limit.

**I get an alert — will I get it again and again?**
No. Each stock alerts **once per day**. If it keeps moving, you won't be spammed.

**What does "previous trading day's close" mean?**
The stock's price at the end of the last day the market was open. The alert fires
when the current price is more than your threshold away from that.

**I don't want a GitHub account — is there another way?**
Yes, but then your computer must stay on during market hours. See `LOCAL_MODE.md`.

---

## For developers / running without GitHub

### Files
| File | Purpose |
|------|---------|
| `app.py` | Local setup web page (run this via `start.bat`) |
| `monitor.py` | The core checker (prices + Telegram alert) |
| `config_local.json` | Your portfolio (tickers, threshold, enabled, provider) — committed |
| `secrets_local.json` | Telegram token, chat id, API key — **git-ignored** |
| `start.bat` | **One-click launcher** — installs deps, opens the setup page |
| `build_exe.bat` | *Optional:* build a single `.exe` (needs PyInstaller) |
| `.github/workflows/monitor.yml` | Free 24/7 cloud scheduler |

### Local-only mode (no GitHub)
If you want to run on your own computer instead of the cloud:
```
start.bat            # set up + enable
python monitor.py    # run one check now
```
To keep it running, you'd need to schedule `monitor.py` to run every 10 min
(e.g. Windows Task Scheduler) and keep the computer on during market hours.

### Optional: build a single `.exe` (if you prefer no Python install)
The `.bat` approach above is lighter and simpler. But if you'd rather give friends
a single file that needs no Python at all, you can build an `.exe`:
```
pip install pyinstaller
build_exe.bat
```
The single-file app appears at `dist\PortfolioIsMoving.exe`.
