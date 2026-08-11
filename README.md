# 📈 PortfolioIsMoving — Setup Guide

**Welcome! This guide walks you through everything, step by step. No technical
knowledge needed. Just follow the steps in order.**

This app watches your stocks and sends you a **Telegram message on your phone**
when a stock moves more than a percentage you choose (default **5%**) from the
previous day's close. It runs **24/7 in the cloud for free** — your computer can
be **off** after you finish setting it up.

---

## What you'll need (all free)

1. **A computer with Windows** (just for the one-time setup)
2. **A phone with Telegram** (to receive alerts)
3. **A free GitHub account** (so it runs 24/7 in the cloud)
4. **One or two free API keys** (for live stock prices)
5. **Your stock tickers** (the short codes, e.g. `HUIZ`, `AAPL`)

---

# PART 1 — Install Python (one time)

> Only do this if you don't already have Python. If you're unsure, just try
> Part 2 first — if it opens the setup screen, you already have Python.

1. Go to **https://www.python.org/downloads/**
2. Click the big yellow **"Download Python"** button.
3. Open the downloaded file.
4. **IMPORTANT:** tick the box **"Add Python to PATH"** at the bottom.
5. Click **"Install Now"** and wait for it to finish.

---

# PART 2 — Open the app

1. **Unzip** the folder you received (right-click → Extract All).
2. **Double-click `start.bat`** inside the folder.
3. A small black window opens, then your **browser opens the app**.
   - If the browser doesn't open, type `http://localhost:8000` into the address bar.
4. You'll see the **Health Check** panel and the setup boxes. Leave it open.

---

# PART 3 — Get your free API key (for live prices)

The app needs a key to fetch **live** stock prices. Pick **one** of these two
(both are free and real-time). **Finnhub is the recommended default.**

### Option A: Finnhub (recommended)
1. Go to **https://finnhub.io/register** and sign up (free, email only).
2. After signing in, your **API key** is on the **Dashboard** page.
3. Copy it. It looks like a long string of letters and numbers.

### Option B: Twelve Data
1. Go to **https://twelvedata.com/register** and sign up (free, email only).
2. After signing in, your **API key** is on the **Account** page.
3. Copy it.

> **Important:** keep your key private. Don't share it. It's like a password.

---

# PART 4 — Create your Telegram bot (for alerts)

This is how alerts reach your phone. **Free, ~3 minutes.** You'll do this on your
**phone** in the Telegram app.

---

### Step 4.1 — Open Telegram on your phone

1. Find the **Telegram** app on your phone (the blue circle with a white paper-plane).
2. Tap it to open it.
3. If you're not already signed in, enter your phone number and follow the steps.

---

### Step 4.2 — Find BotFather

1. At the **top** of the Telegram screen, there's a **search bar** (a magnifying-glass
   icon ⚙ or a "Search" box).
2. Tap it and type: **`@BotFather`**
3. Tap the result that says **"BotFather"** with a **blue checkmark** next to it.
   - It's the OFFICIAL bot. Don't tap any other "BotFather" without the checkmark.

---

### Step 4.3 — Create a new bot

1. You'll see a chat window with BotFather.
2. At the **bottom**, there's a **message box** (where you type messages).
3. Type this exactly and press **Send** (the paper-plane icon):
   ```
   /newbot
   ```
4. BotFather asks: *"Alright, a new bot. How are we going to call it?"*
   - Type a **name** for your bot (any name, e.g. `My Stock Alerts`). Press Send.
5. BotFather asks: *"Now let's choose a username for your bot. It must end in bot."*
   - Type a **username** that ends in `bot`, e.g. `mystockalerts_bot`. Press Send.
   - If it says the username is taken, try another one.
6. BotFather replies with a message containing your **token**. It looks like:
   ```
   123456789:AAH...
   ```
   - This is a long string of letters and numbers.
   - **Copy it** (tap and hold → Copy). Keep it somewhere safe.

---

### Step 4.4 — Get your chat id (auto)

Now you need to "talk" to your bot once, so Telegram knows you want to receive
messages from it. **This is where the "Start" button is.**

1. At the **top**, tap the **search bar** again.
2. Type your bot's **username** (e.g. `@mystockalerts_bot`).
3. Tap your bot in the results — it opens a chat window with your bot.
4. At the **bottom** of that chat, you'll see a blue button that says:
   **"START"** (and usually a "🚀" or "▶️" icon).
   - **Tap that START button.**
5. After tapping Start, you'll see a **message box** at the bottom.
   - Type `hi` and press **Send** (the paper-plane icon).
   - Your bot will reply something like *"I don't understand..."* — that's fine.
6. Now go to the **app** (still open in your browser on your computer).
   - In the **Telegram** box, paste your **bot token** (from Step 4.3).
   - Click the **"🪪 Get my chat id"** button.
   - The app will find and fill in your **chat id** automatically. 🎉

> 📌 **If the button says "No message found yet":** you didn't press Start or send
> a message. Go back to Step 4.4, tap **START**, send `hi`, then click the button again.

> 📌 **Manual way (only if the button never works):**
> 1. On your computer, open a new browser tab and go to:
>    `https://api.telegram.org/botYOUR_TOKEN_HERE/getUpdates`
>    (replace `YOUR_TOKEN_HERE` with your actual token)
> 2. You'll see a page of text. Look for this pattern: `"chat":{"id":123456789`
> 3. The number right after `"id":` is your **chat id**. Copy it and paste it
>    into the app's **Chat ID** box.

---

# PART 5 — Fill in the setup screen

In the app (still open in your browser), fill in the boxes:

1. **Your stocks** — type a ticker (e.g. `HUIZ`) and click **Add**. Add up to
   10-12 stocks. (A ticker is the short code for a stock. If unsure, search
   "stock ticker for \<company name\>".)
2. **Alert threshold** — leave at **5** (means "alert when it moves more than 5%").
3. **Price source** — choose your provider (Finnhub or Twelve Data). Paste your
   API key from Part 3.
4. **Telegram** — paste your **bot token**, click **"🪪 Get my chat id"** to fill
   the chat id, then click **"📲 Send test alert"** — you should get a Telegram
   message on your phone. If not, double-check the token and chat id.
5. **Enable monitoring** — switch it **ON**.
6. Click **🩺 Run health check** at the top — it should all show green/OK.
7. Click **💾 Save portfolio**.

**Done with the app!** You can close the black window and browser tab.

---

# PART 6 — Connect to GitHub (so it runs 24/7 for free)

> This is the only slightly technical part. **Follow it slowly, one step at a
> time.** It takes about 5 minutes. Do it once.

**Why this step exists:** Your computer can't stay on 24/7, so a free service
called **GitHub Actions** runs the monitor for you in the cloud. This part
"connects" your setup to that free service.

**What you'll do in this part:**
1. Create a free GitHub account
2. Make a copy ("fork") of this project under your account
3. Tell GitHub your private info (called "secrets")
4. Upload your stock list
5. Turn on the monitor

---

### A. Create a free GitHub account (if you don't have one)

1. Go to **https://github.com/**
2. Click **Sign up** (top-right).
3. Enter an **email**, a **password**, and a **username** (pick anything, e.g. `mystockalerts`).
4. Click **Create account**.
5. GitHub will email you a code — enter it to confirm.
6. Answer the optional questions (or just click **Skip** / **Continue**).

---

### B. Make your own copy of this project

> This is called a **"fork"**. It makes a copy of the project under YOUR account,
> so it's yours to change.

1. Open this project's GitHub page (ask the person who gave you this for the link).
2. Click the **Fork** button (top-right, near the star icon).
3. Wait a few seconds — you now have your own copy at
   `github.com/YOUR_USERNAME/PortfolioIsMoving`.

---

### C. Add your secrets (your private info)

> "Secrets" are how you safely tell GitHub your Telegram token, chat id, and API
> key — WITHOUT showing them to anyone. They're encrypted and only the cloud
> monitor can read them.

1. On **your** copy's page, click the **Settings** tab (near the top, under the
   repo name).
2. In the **left sidebar**, click **Secrets and variables**.
3. Click **Actions**.
4. Click the green **New repository secret** button.
5. A form appears with two boxes: **Name** and **Value**.
6. **First secret:**
   - **Name:** type exactly `TELEGRAM_BOT_TOKEN`
   - **Value:** paste your Telegram bot token (from Part 4)
   - Click **Add secret** (green button).
7. **Second secret:** click **New repository secret** again.
   - **Name:** type exactly `TELEGRAM_CHAT_ID`
   - **Value:** paste your Telegram chat id (from Part 4)
   - Click **Add secret**.
8. **Third secret:** click **New repository secret** again.
   - **Name:** type exactly `FINNHUB_KEY`
   - **Value:** paste your **Finnhub** API key (from Part 3, Option A)
   - Click **Add secret**.
9. **Fourth secret:** click **New repository secret** again.
   - **Name:** type exactly `TWELVEDATA_KEY`
   - **Value:** paste your **Twelve Data** API key (from Part 3, Option B)
   - Click **Add secret**.

> ✅ You should now see 4 secrets listed: `TELEGRAM_BOT_TOKEN`,
> `TELEGRAM_CHAT_ID`, `FINNHUB_KEY`, `TWELVEDATA_KEY`.

> 💡 **Why both keys?** The app supports two providers (Finnhub and Twelve Data),
> and each uses a **different** key. GitHub stores both, and the monitor uses the
> one that matches the provider you chose in the app. If you only use one provider,
> you can leave the other key blank.

> ⚠️ **Copy the names EXACTLY** — with capital letters and underscores. If a name
> is wrong, the monitor can't find it and won't work.

---

### D. Upload your stock list

> Your stock list is in a file called `config_local.json`. It was created when
> you saved in the app (Part 5). You need to upload it to your GitHub copy so the
> cloud monitor knows which stocks to watch.

1. Find `config_local.json` in the folder where you unzipped the app.
2. On **your** GitHub copy, click **Add file** (near the top) → **Upload files**.
3. **Drag** `config_local.json` into the upload area (or click to browse).
4. Scroll down and click **Commit changes** (green button).

> ⚠️ Do **NOT** upload `secrets_local.json` — that file has your private info
> and must stay on your computer.

---

### E. Turn on the monitor

> ⚠️ **Important:** after forking, GitHub **turns OFF** the automatic monitor by
> default. You must turn it on here. If you skip this step, nothing will run.

1. On **your** GitHub copy, click the **Actions** tab (near the top).
2. If GitHub shows a warning, click **"I understand my workflows, go ahead and
   enable them"**.
3. In the left sidebar, click **Monitor Portfolio**.
4. Click the **Run workflow** button (right side, near the top).
5. Click the green **Run workflow** button in the dropdown.
6. A run appears in the list. Click it to watch it work.
7. In the run, click the **Monitor** job, then the step **Run monitor**.
8. You'll see the log — it checks each of your stocks and shows their % move.

---

**That's it!** Your monitor is now connected and runs automatically **every 10
minutes during US market hours (Mon–Fri, 9:30am–4pm ET)**. Your computer can be
off — the cloud does the work.

> 💡 **Make sure your own stocks are in the config.** The copy starts with example
> tickers. After you set your own stocks in the app and save, upload the new
> `config_local.json` (step D). The monitor uses whatever is in that file.

---

# When you want to change your stocks

1. Run `start.bat` again → change your tickers / threshold → **Save**.
2. Re-upload the new `config_local.json` to your GitHub copy (Part 6, step D).
3. Done — the monitor uses the new list on its next run.

---

# FAQ

**Does my computer need to stay on?**
No. After setup, everything runs in the cloud. Turn your computer off.

**Is it really free?**
Yes. Telegram is free. GitHub Actions is free for public repos. The price APIs are
free (with limits). See the limits below.

**How fast is the alert?**
Checked every 10 minutes. **Finnhub** and **Twelve Data** are real-time. **Yahoo**
(no key) is ~15 min delayed. All fine for stocks that move over hours.

**How many stocks can I track for free?**
- **Finnhub** (default): up to **50** stocks. 60 calls/min, no daily cap.
- **Twelve Data**: up to **8** per check, ~**20/day**. 800/day limit.
- **Yahoo**: up to **50**. No hard limit.

**Will I get spammed?**
No. Each stock alerts **once per day**. If it keeps moving, you won't get more
messages for it that day.

**What does "previous trading day's close" mean?**
The stock's price at the end of the last day the market was open. The alert fires
when the current price is more than your threshold away from that.

**I don't want a GitHub account — is there another way?**
Yes, but then your computer must stay on during market hours. See `LOCAL_MODE.md`.

**Why does the app show "unlimited" for per-day on Finnhub/Yahoo?**
Because those providers have **no daily limit** (only a per-minute limit, or none
at all). Only Twelve Data has a real daily cap (800/day), which the app tracks.

---

# Troubleshooting

| Problem | What to do |
|---------|-----------|
| No browser opens | Type `http://localhost:8000` into the address bar. |
| "Python is not installed" | Install Python (Part 1). Tick "Add Python to PATH". |
| Test alert doesn't arrive | Check the token and chat id are pasted exactly (no spaces). Press **Start** on your bot. |
| Health check shows price error | Your API key may be wrong. Check Part 3 and re-paste it. |
| No alerts during the day | Check your GitHub Actions log (Part 6, step E). Common cause: secrets missing, or monitoring off. |

---

# Need more detail?

- **`README-DEVELOPER.md`** — for developers.
- **`README-TECHNICAL.md`** — full technical reference / for AI.
- **`LOCAL_MODE.md`** — how to run without GitHub (computer must stay on).
