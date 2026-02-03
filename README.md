# Deal Diligence OS

> A Telegram-driven personal operating system for research, finance tracking, journaling, and habit RPG—built on Raspberry Pi, Notion, and Perplexity AI.
> **Featured Project** - As seen on LinkedIn | 

[![GitHub stars](https://img.shields.io/github/stars/brianj0108-netizen/deal-diligence-os-public?style=social)](https://github.com/brianj0108-netizen/deal-diligence-os-public)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue)](https://linkedin.com/in/brian-john-51215132b/)
---
## ⚖️ Legal Disclaimer

**This is an educational project demonstrating API integration and automation. NOT financial advice.**

- Stock analysis features are for **informational purposes only**
- Do NOT make investment decisions based on this tool
- Consult a licensed financial advisor before investing
- The creator is not liable for any financial losses
- By using this code, you agree to use it at your own risk

This tool does not constitute investment advice, and the creator is not a registered investment advisor.


## Overview

**Deal Diligence OS** is a 24/7 Telegram bot that acts as your personal assistant, integrating:

- **Deep-dive research reports** (via Perplexity AI, delivered as HTML emails)
- **Real-time stock analysis** (Telegram summaries + optional email reports)
- **Paycheck allocation tracker** (logs income splits into Notion: Needs/Wants/Debt/Savings)
- **Life RPG & Journal** (logs daily activities into Notion with a simple XP/class system)
- **Automated workout scheduler** (sends workout plans on a schedule you define)

All of this runs on a **Raspberry Pi Zero W** using systemd, with no GUI required.

---

## Tech Stack

- **Python 3.9+** (main bot logic)
- **Telegram Bot API** (HTTP polling, no webhooks)
- **Perplexity API** (via OpenAI client) for research and stock analysis
- **Notion API** for database reads/writes (RPG, Journal, Paycheck Tracker)
- **Gmail SMTP** for HTML email delivery
- **systemd** (keeps the bot running 24/7 on Linux)

---

## Features

### 1. Research & Stock Analysis

- **`research [topic]`**  
  Generates a comprehensive HTML report (Overview, Recent Developments, Fundamentals, Risks, Conclusion) and emails it to you.

- **Natural stock questions**  
  Ask "is TSLA a good buy?" or "should I invest in NVDA?" and get:
  - A Telegram summary (quick take with current price, news, recommendation)
  - A full HTML email report with technical and fundamental analysis

### 2. Paycheck Tracker

- **`paycheck [amount]`**  
  Logs a paycheck into a Notion database with a simple allocation:
  - **50% Needs** (rent, bills, groceries)
  - **20% Wants** (fun, lifestyle)
  - **15% Debt** (loans / credit cards)
  - **15% Savings** (emergency fund or short-term goals)
  - **Investments** column (default 0; you can adjust)

  **Customize the buckets and percentages** by editing `save_paycheck_to_notion()` in `src/telegram_brain.py`.

### 3. Life RPG & Journal

- **`J: [text]`**  
  Saves to your **Private Journal** database in Notion (for personal reflections).

- **Any other text message**  
  Saves to the **Life RPG** database with:
  - A "Quest" title (first 100 chars of your message)
  - A **Class** (Saver, Scholar, Athlete, Creator, Explorer)
  - **XP** earned (10–50 points depending on activity type)

  **Classes are auto-detected** based on keywords:
  - **Saver** (50 XP): saving, budgeting, investing
  - **Scholar** (30 XP): studying, exams, learning
  - **Athlete** (30 XP): workouts, gym, running
  - **Creator** (20 XP): building, writing, creating
  - **Explorer** (10 XP, default): everything else

  **Customize classes/XP** by editing `detect_rpg_class()` in `src/telegram_brain.py`.

### 4. Automated Workout Scheduler

- **`src/titan_trainer.py`**  
  Sends pre-planned workouts to your Telegram on a schedule (e.g., Mon/Wed/Fri).

  **Customize workouts** by editing the `WORKOUT_PLANS` dictionary at the top of `titan_trainer.py`:

  ```python
  WORKOUT_PLANS = {
      "monday": "Upper Body A:\n- Bench Press 3x8\n- Row 3x10",
      "wednesday": "Lower Body:\n- Squats 3x8\n- RDL 3x10",
      # Add more days as needed
  }
Schedule it using cron or systemd (see docs/ for examples).

Setup
Prerequisites
A Telegram bot (create via @BotFather; save your token)

A Notion workspace with three databases:

Life RPG (columns: Quest [title], Date [date], Topic [multi-select], Class [select], XP [number], AUM [number])

Private Journal (columns: Name [title], Date [date])

Paycheck Tracker (columns: Check # [title], Date [date], Net Amount [number], Needs [number], Wants [number], Debt [number], Savings [number], Investments [number])

Notion integration (create at notion.so/my-integrations
; save the secret)

Perplexity API key (sign up at perplexity.ai
)

Gmail app password (for SMTP; see Google support)

Installation
Clone this repo

bash
git clone https://github.com/brianj0108-netizen/deal-diligence-os-public.git
cd deal-diligence-os-public
Copy the example keys file and fill in your credentials

bash
cp keys.example.txt keys.local.txt
nano keys.local.txt  # or any editor
Fill in:

TELEGRAM_TOKEN

TELEGRAM_CHAT_ID (your Telegram user ID; send /start to @userinfobot)

NOTION_KEY

RPG_DATABASE_ID, JOURNAL_DATABASE_ID, PAYCHECK_DATABASE_ID

PERPLEXITY_KEY

EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECEIVER

Install Python dependencies

bash
pip3 install requests openai
Test the bot manually

bash
cd src
python3 telegram_brain.py
Send a test message to your bot on Telegram. If it responds, setup is working.

Run 24/7 with systemd (Linux/Pi)
Create a service file (e.g., /etc/systemd/system/telegram-brain.service):

text
[Unit]
Description=Deal Diligence OS - Telegram Brain
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/home/YOUR_USERNAME/deal-diligence-os-public/src
ExecStart=/usr/bin/python3 -u /home/YOUR_USERNAME/deal-diligence-os-public/src/telegram_brain.py
Restart=always

[Install]
WantedBy=multi-user.target
Enable and start:

bash
sudo systemctl daemon-reload
sudo systemctl enable telegram-brain.service
sudo systemctl start telegram-brain.service
(Optional) Schedule workouts
To run titan_trainer.py on specific days, add a cron job or systemd timer:

Cron example (Mon/Wed/Fri at 6 AM):

text
0 6 * * 1,3,5  /usr/bin/python3 /home/YOUR_USERNAME/deal-diligence-os-public/src/titan_trainer.py
Usage
Once the bot is running, message it on Telegram:

Command	Result
/help or triggers	Show the command guide
research AI chips	Email you a deep-dive report on AI chips
is AAPL a good buy?	Telegram summary + email with stock analysis
paycheck 1500	Log $1,500 paycheck into Notion with Needs/Wants/Debt/Savings split
J: Feeling grateful today	Save to Private Journal DB
Saved $200 to emergency	Save to Life RPG as "Saver" class, 50 XP
Studied 2 hours for exam	Save to Life RPG as "Scholar" class, 30 XP
Gym: upper body A	Save to Life RPG as "Athlete" class, 30 XP
Customization
Paycheck Buckets
Edit save_paycheck_to_notion() in src/telegram_brain.py:

python
alloc = {
    "Needs": round(net_amount * 0.50, 2),   # Change % here
    "Wants": round(net_amount * 0.20, 2),
    "Debt": round(net_amount * 0.15, 2),
    "Savings": round(net_amount * 0.15, 2),
}
And update the properties dict to match your Notion column names.

RPG Classes
Edit detect_rpg_class() in src/telegram_brain.py:

python
if any(x in lower for x in ["save", "saving", "budget", "invest"]):
    return {"Class": {"select": {"name": "Saver"}}, "XP": {"number": 50}}
# Add more conditions or change XP values
Workout Plans
Edit WORKOUT_PLANS in src/titan_trainer.py:

python
WORKOUT_PLANS = {
    "monday": "Your Monday routine here...",
    "tuesday": "Your Tuesday routine here...",
}
No Python knowledge required—just edit the text inside the triple quotes.

Project Structure
text
deal-diligence-os-public/
├── .gitignore
├── keys.example.txt           # Template for secrets (not committed)
├── README.md
└── src/
    ├── config_public.py       # Loads keys from keys.local.txt
    ├── telegram_brain.py      # Main bot (research, stock, RPG, paycheck)
    └── titan_trainer.py       # Workout scheduler
Why This Project?
I built this to solve a personal problem: I wanted a single Telegram interface for:

Deep research without opening a browser

Quick stock takes when I'm on the go

Automatic paycheck budgeting into Notion

A gamified way to track life progress (RPG + XP system)

Consistent workout reminders without manual planning

Running it on a Raspberry Pi Zero W keeps it always-on, low-cost, and a great learning exercise in Linux, systemd, API integrations, and Python automation.

Roadmap / Future Ideas
 Add voice message transcription (Whisper API)

 Integrate calendar (Google Calendar API) for auto-scheduling

 Add expense tracking (OCR receipt scanning)

 Build a web dashboard (Flask/FastAPI + React)

 Multi-user support (different Telegram chat IDs → separate Notion workspaces)

Contributing
This is a personal project/portfolio piece, but if you fork it and build something cool, feel free to open a PR or just share what you made. I'd love to see it.


Contact
Questions? Ideas? Want to hire me to build something similar for you?

GitHub: @BrianJ0108-netizen

LinkedIn: linkedin.com/in/brian-john-51215132b/


Acknowledgments
Perplexity AI for the research + stock analysis engine

Notion for the flexible database + API

Built with ☕ and late-night coding sessions on a Raspberry Pi Zero W.

Telegram for the clean bot API

The open-source Python community (requests, OpenAI client, etc.)
