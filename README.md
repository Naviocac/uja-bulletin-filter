# uja-bulletin-filter

Filters the daily UJA (University of Jaén) bulletin and notifies you on
Telegram only when something is actually worth reading, instead of having
to skim 10 activities every day.

## How it works

1. **Extraction** (`src/gmail_extractor.py`) — reads the bulletin email from Gmail.
2. **AI filter** (`src/llm_filter.py`) — compares each activity against your
   preferences (stored in `preferences.json`) using Jev, a typed-decision
   model from TypeSafe AI.
3. **Notification** (`src/telegram_bot.py`) — sends the summary via Telegram.
4. **Automation** — GitHub Actions runs the whole pipeline every morning.

## Project status

Track progress on the repo's Project board (Todo / In Progress / Done),
or see `ROADMAP.md` for the full task list.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in your own values
```

You need a `credentials.json` from Google Cloud (Gmail API, OAuth desktop
client) in the project root. The first time you run the extractor it will
open your browser to authorize access, and a `token.json` will be saved
for next time.

You also need a `TYPESAFE_API_KEY` (see https://console.typesafe.ai) for
the AI filter to work.
