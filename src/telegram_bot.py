"""
telegram_bot.py

Sends a message to your Telegram chat using the bot created with
@BotFather. No extra dependency needed — just a plain HTTP request to
Telegram's Bot API.

Usage:
    python src/telegram_bot.py          (sends a test message)
"""

import os

import requests
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def send_message(text):
    """Sends `text` to your Telegram chat. Returns True on success."""
    if not BOT_TOKEN or not CHAT_ID:
        raise RuntimeError(
            "Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID in your .env file."
        )

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "disable_web_page_preview": True,
    }

    response = requests.post(url, data=payload, timeout=10)

    if not response.ok:
        print("Telegram API error:", response.text)
        return False

    return True


if __name__ == "__main__":
    ok = send_message("uja-bulletin-filter: this is a test message. If you see this, the bot works.")
    print("Message sent!" if ok else "Failed to send message.")