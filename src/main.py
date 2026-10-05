"""
main.py

Runs the full pipeline once: fetch every bulletin received in the last 24h
(usually one, occasionally two), split them into activities, then for each
subscriber in data/subscribers.json, filter those activities against their
own chosen interests with Jev, and send them their own personalized
Telegram summary.

Usage:
    python src/main.py
"""

import json
import os

from activity_filter import filter_activities
from bulletin_parser import parse_activities
from categories import build_preference_text
from gmail_extractor import fetch_bulletins
from telegram_bot import send_message

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUBSCRIBERS_PATH = os.path.join(BASE_DIR, "data", "subscribers.json")


def load_subscribers():
    if not os.path.exists(SUBSCRIBERS_PATH):
        return {}
    with open(SUBSCRIBERS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def build_summary(relevant_activities):
    """Turns the filtered activities into the message the bot will send."""
    if not relevant_activities:
        return "Hoy no hay nada interesante."

    lines = [f"{len(relevant_activities)} actividad(es) podrían interesarte:\n"]
    for a in relevant_activities:
        lines.append(f"• {a['title']}")
        if a.get("url"):
            lines.append(f"  {a['url']}")
    return "\n".join(lines)


def run():
    bulletins = fetch_bulletins()

    if not bulletins:
        print("No new bulletin found today.")
        return

    print(f"Found {len(bulletins)} bulletin(s) today.")

    # Gather activities from every bulletin found (usually 1, sometimes 2+)
    all_activities = []
    for html in bulletins:
        all_activities.extend(parse_activities(html))

    print(f"Extracted {len(all_activities)} activities in total.\n")

    subscribers = load_subscribers()
    if not subscribers:
        print("No subscribers yet — nothing to send. People can /start the bot on Telegram.")
        return

    for chat_id, subscriber in subscribers.items():
        preferences = build_preference_text(subscriber.get("interests", {}))
        if preferences is None:
            print(f"{chat_id}: hasn't chosen any interests yet, skipping.")
            continue

        relevant = filter_activities(all_activities, preferences=preferences)
        summary = build_summary(relevant)

        sent = send_message(chat_id, summary)
        status = "sent" if sent else "FAILED to send"
        print(f"{chat_id}: {status} ({len(relevant)} relevant activities)")

    print("\nDone.")


if __name__ == "__main__":
    run()