"""
bulletin_parser.py

Splits the UJA bulletin's HTML into individual activities (category, title,
description, link), based on the structure Mailchimp uses for this specific
newsletter:

    <span style="...background-color:#008000...">Category</span>   <- category
    ...
    <a style="...color: #006d38...">Title</a>                      <- title + link
    <h4 style="...color: #202020...">Description</h4>               <- description

If the UJA ever changes the newsletter's template, this is the file to
adjust — the parsing logic is isolated here on purpose, separate from the
Gmail extraction code.

Usage:
    python src/bulletin_parser.py   (parses data/latest_bulletin.html)
"""

import os

from bs4 import BeautifulSoup

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_HTML_PATH = os.path.join(BASE_DIR, "data", "latest_bulletin.html")

# Styling fingerprints used to find each element reliably, even though
# these are plain <span>/<a>/<h4> tags with no id or class of their own.
CATEGORY_STYLE_HINT = "background-color:#008000"
TITLE_STYLE_HINT = "#006d38"


def parse_activities(html):
    """Returns a list of {"category", "title", "description", "url"} dicts,
    one per activity found in the bulletin's HTML."""
    soup = BeautifulSoup(html, "html.parser")

    title_links = soup.find_all(
        "a", style=lambda s: s and TITLE_STYLE_HINT in s
    )

    activities = []
    for link in title_links:
        category_tag = link.find_previous(
            "span", style=lambda s: s and CATEGORY_STYLE_HINT in s
        )
        description_tag = link.find_next("h4")

        activities.append(
            {
                "category": category_tag.get_text(strip=True) if category_tag else None,
                "title": link.get_text(strip=True),
                "description": description_tag.get_text(strip=True) if description_tag else "",
                "url": link.get("href"),
            }
        )

    return activities


if __name__ == "__main__":
    if not os.path.exists(DEFAULT_HTML_PATH):
        print(f"No file found at {DEFAULT_HTML_PATH}. Run gmail_extractor.py first.")
    else:
        with open(DEFAULT_HTML_PATH, encoding="utf-8") as f:
            html = f.read()

        activities = parse_activities(html)

        print(f"Found {len(activities)} activities:\n")
        for a in activities:
            print(f"[{a['category']}] {a['title']}")
            print(f"  {a['description'][:120]}...")
            print()