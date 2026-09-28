# Roadmap

Task list for the project. This same list is turned into GitHub Issues
and organized on a board (To Do / In Progress / Done) by this script.

## Phase 1 — Email extraction
- [x] Create `gmail_extractor.py` (reads the bulletin from Gmail)
- [ ] Set up Gmail OAuth credentials (`credentials.json`)
- [ ] Test the extractor with your real bulletin
- [ ] Adjust the extractor if the bulletin's HTML is inconsistent

## Phase 2 — AI integration
- [x] Write `activity_filter.py` using Jev (TypeSafe AI)
- [ ] Get a TypeSafe API key and confirm the filter works
- [ ] Tune preferences.json and the relevance threshold
- [ ] Connect the real extracted bulletin text to the filter (split into activities)

## Phase 3 — Telegram bot
- [ ] Create the bot with @BotFather and save the token
- [ ] Write `telegram_bot.py`
- [ ] Format the final message ("nothing interesting today" / "3 activities...")
- [ ] Test sending it manually

## Phase 4 — Deployment and automation
- [ ] Write `main.py` (ties extraction + filter + notification together)
- [ ] Set up Secrets on GitHub (tokens and keys, never hardcoded)
- [ ] Create `.github/workflows/daily.yml`
- [ ] Confirm it runs automatically every morning

## Future ideas (optional)
- [ ] Support for a traditional LLM (Gemini/Groq) as a fallback
- [ ] Telegram command to update your preferences without touching code
- [ ] History of already-notified activities (to avoid repeats)
