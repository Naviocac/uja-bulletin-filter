"""
main.py

Runs the full pipeline once: fetch today's bulletin from Gmail, split it
into activities, filter them with Jev against your preferences, and print
the result — a preview of what the Telegram bot will eventually send.

Usage:
    python src/main.py
"""

from activity_filter import filter_activities
from bulletin_parser import parse_activities
from gmail_extractor import fetch_latest_bulletin


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
    html = fetch_latest_bulletin()

    if html is None:
        print("No new bulletin found today.")
        return

    activities = parse_activities(html)
    print(f"Extracted {len(activities)} activities from today's bulletin.\n")

    relevant = filter_activities(activities)

    print(build_summary(relevant))


if __name__ == "__main__":
    run()