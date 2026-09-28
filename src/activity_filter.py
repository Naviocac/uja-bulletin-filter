"""
activity_filter.py

Compares each activity from the bulletin against your stored preferences
using Jev (TypeSafe AI): one typed "is this relevant?" (Noul) judgment per
activity, all evaluated together in a single request.

Note: Jev is a very new, early-access API (launched Sept 2026). The SDK
interface below matches the official docs at the time of writing, but as
an early-access product it can change — check https://docs.typesafe.ai if
something doesn't match.

Usage:
    python src/activity_filter.py   (runs on the sample activities below)
"""

import json
import os

from dotenv import load_dotenv
from typesafe_sdk import Noul, TypeSafeClient

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PREFERENCES_PATH = os.path.join(BASE_DIR, "preferences.json")

# A judgment at or above this probability counts as "worth notifying about"
RELEVANCE_THRESHOLD = 0.6


def load_preferences():
    """Reads your stated interests from preferences.json."""
    if not os.path.exists(PREFERENCES_PATH):
        return "No preferences set yet — treat everything as potentially interesting."

    with open(PREFERENCES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data.get("interests", "")


def filter_activities(activities, preferences=None):
    """
    activities: list of dicts like {"title": ..., "description": ...}

    Returns the subset Jev judged relevant to your preferences, each
    tagged with its relevance probability (0-1), sorted highest first.
    """
    if preferences is None:
        preferences = load_preferences()

    if not activities:
        return []

    # One Noul question per activity, all sent together in a single call
    questions = {}
    for i, activity in enumerate(activities):
        key = f"activity_{i}"
        questions[key] = Noul(
            instructions=(
                f"The user's stated interests are: {preferences}\n\n"
                "Does the following activity clearly match any of those interests?\n\n"
                f"Title: {activity['title']}\n"
                f"Description: {activity.get('description', '')}"
            )
        )

    with TypeSafeClient() as client:  # reads TYPESAFE_API_KEY from the environment
        response = client.system_one(state={}, questions=questions)

    relevant = []
    for i, activity in enumerate(activities):
        probability = response.answers[f"activity_{i}"].noul
        if probability >= RELEVANCE_THRESHOLD:
            relevant.append({**activity, "relevance": probability})

    relevant.sort(key=lambda a: a["relevance"], reverse=True)
    return relevant


if __name__ == "__main__":
    sample_activities = [
        {
            "title": "Erasmus+ scholarship call for 2026/2027",
            "description": "Applications open for mobility grants at European universities.",
        },
        {
            "title": "Introduction to padel workshop",
            "description": "Sports activity organized by the University Sports Service.",
        },
        {
            "title": "Seminar on Artificial Intelligence applied to healthcare",
            "description": "Talk on AI models for medical diagnosis, organized by the Computer Science department.",
        },
    ]

    results = filter_activities(sample_activities)

    if not results:
        print("Nothing interesting today.")
    else:
        print(f"{len(results)} activity(ies) might interest you:\n")
        for r in results:
            print(f"- {r['title']} (relevance: {r['relevance']:.2f})")
