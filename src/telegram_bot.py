"""
telegram_bot.py

Sends a message to a given Telegram chat using the bot created with
@BotFather. No extra dependency needed — just a plain HTTP request to
Telegram's Bot API.

Usage:
    python src/telegram_bot.py          (sends a test message to TELEGRAM_CHAT_ID,
                                          if that's still set in your .env — useful
                                          for a quick manual check)
"""

import os

import requests
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


def send_message(chat_id, text):
    """Sends `text` to the given Telegram chat_id. Returns True on success."""
    if not BOT_TOKEN:
        raise RuntimeError("Missing TELEGRAM_BOT_TOKEN in your .env file.")

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": True,
    }

    response = requests.post(url, data=payload, timeout=10)

    if not response.ok:
        print("Telegram API error:", response.text)
        return False

    return True


if __name__ == "__main__":
    test_chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not test_chat_id:
        print("Set TELEGRAM_CHAT_ID in your .env to send a one-off test message.")
    else:
        ok = send_message(
            test_chat_id,
            "uja-bulletin-filter: this is a test message. If you see this, the bot works.",
        )
        print("Message sent!" if ok else "Failed to send message.")