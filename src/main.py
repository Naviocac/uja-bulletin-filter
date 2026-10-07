"""
main.py

Runs the full pipeline once: fetch every bulletin received in the last 24h
(usually one, occasionally two), split them into activities, filter them
with Jev against your preferences, and send the result to Telegram.

Usage:
    python src/main.py
"""

from activity_filter import filter_activities
from bulletin_parser import parse_activities
from gmail_extractor import fetch_bulletins
from telegram_bot import send_message


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

    relevant = filter_activities(all_activities)
    summary = build_summary(relevant)

    print(summary)

    sent = send_message(summary)
    print("\nSent to Telegram!" if sent else "\nCould not send the message to Telegram.")


if __name__ == "__main__":
    run()