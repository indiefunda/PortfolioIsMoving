# Local Mode (no GitHub account needed)

If you **don't** want a GitHub account, you can run the monitor on **your own
computer**. The catch: **your computer must be on during US market hours**
(9:30 am – 4:00 pm Eastern, Mon–Fri) for alerts to fire.

You only need this if you can't or won't create a GitHub account. The
cloud (GitHub Actions) method described in the main README is better because it
runs 24/7 even when your computer is off.

---

## How to run locally

1. **Install Python** (see main README, Step 1).
2. **Open the setup screen** — double-click `start.bat`, set your tickers,
   threshold, Telegram token + chat id, enable monitoring, and **Save**.
3. **Schedule it to run every 10 minutes** using Windows Task Scheduler:

### Set up Windows Task Scheduler (once)

1. Press **Windows + R**, type `taskschd.msc`, press Enter.
2. Click **Create Task** (right panel).
3. **General tab:** Name it `PortfolioIsMoving`. Tick **"Run whether user is logged on or not"**.
4. **Triggers tab:** click **New** → **Begin the task**: *On a schedule* →
   **Daily** → set a start time like 9:25 AM → tick **"Repeat task every"** → set to `10 minutes` →
   **for a duration of** `1 day`. Click OK.
5. **Actions tab:** click **New** → Action: *Start a program* →
   **Program/script:** browse to your Python (`python.exe`) →
   **Add arguments:** `monitor.py` →
   **Start in:** the folder containing this project (e.g. `F:\MyRepository\PortfolioIsMoving`).
6. Click OK. When prompted for a password, enter your Windows login.

Now it checks every 10 minutes while your computer is on.

---

## To stop it
- Open **Task Scheduler**, right-click `PortfolioIsMoving`, and **Disable** or **Delete**.

## Important
- Your computer must be **on and not asleep** during market hours.
- Keep `secrets_local.json` private — it holds your Telegram token.
