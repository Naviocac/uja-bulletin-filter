"""
gmail_extractor.py

Connects to Gmail and finds every UJA bulletin email from the last 24h
(there's usually one per day, but occasionally two). Returns a list of
raw HTML bodies, ready to be split into activities by bulletin_parser.py.

Uses the Gmail API's "raw" format + Python's standard email library instead
of the "full" format, because "full" was returning bodies with broken
accented characters (Gmail re-encodes them incorrectly in that format).
Parsing the raw MIME message ourselves respects each part's real charset.

Usage:
    python src/gmail_extractor.py
"""

import base64
import os
from email import message_from_bytes

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

load_dotenv()

# Read-only: the script can never delete or send emails.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

_sender = os.getenv("BULLETIN_SENDER_EMAIL", "boletin@uja.es")
GMAIL_QUERY = f"from:{_sender} newer_than:1d"

# Safety cap on how many bulletin emails we'll process in one run — the UJA
# normally sends one a day, occasionally two, so this is generous headroom.
MAX_RESULTS = 10

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CREDENTIALS_PATH = os.path.join(BASE_DIR, "credentials.json")
TOKEN_PATH = os.path.join(BASE_DIR, "token.json")


def get_gmail_service():
    """Authenticates with Google (or reuses the saved token) and returns
    a Gmail API client."""
    creds = None

    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_PATH, SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open(TOKEN_PATH, "w") as token_file:
            token_file.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def _extract_bodies(mime_message):
    """Walks every part of the parsed email and returns (html, plain),
    decoding each part with ITS OWN declared charset (falls back to utf-8),
    which is what actually fixes the broken accented characters."""
    html = None
    plain = None

    for part in mime_message.walk():
        content_type = part.get_content_type()
        if part.is_multipart():
            continue

        charset = part.get_content_charset() or "utf-8"
        payload = part.get_payload(decode=True)
        if payload is None:
            continue

        text = payload.decode(charset, errors="replace")

        if content_type == "text/html" and html is None:
            html = text
        elif content_type == "text/plain" and plain is None:
            plain = text

    return html, plain


def fetch_bulletins():
    """Finds every bulletin email from the last 24h and returns a list of
    their raw HTML bodies (oldest first). Returns an empty list if there's
    no new bulletin. Also saves each one to data/bulletin_<message_id>.html
    and the most recent one to data/latest_bulletin.html, for debugging."""
    service = get_gmail_service()

    results = (
        service.users()
        .messages()
        .list(userId="me", q=GMAIL_QUERY, maxResults=MAX_RESULTS)
        .execute()
    )
    messages = results.get("messages", [])

    if not messages:
        return []

    # Gmail lists newest first; process oldest first so summaries read in
    # chronological order if there happen to be two bulletins in one day.
    messages = list(reversed(messages))

    bodies = []
    os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)

    for message in messages:
        raw_message = (
            service.users()
            .messages()
            .get(userId="me", id=message["id"], format="raw")
            .execute()
        )
        raw_bytes = base64.urlsafe_b64decode(raw_message["raw"])
        mime_message = message_from_bytes(raw_bytes)

        html, plain = _extract_bodies(mime_message)
        content = html or plain

        if content is None:
            continue

        bodies.append(content)

        filename = f"bulletin_{message['id']}.html" if html else f"bulletin_{message['id']}.txt"
        with open(os.path.join(BASE_DIR, "data", filename), "w", encoding="utf-8") as f:
            f.write(content)

    if bodies:
        with open(
            os.path.join(BASE_DIR, "data", "latest_bulletin.html"),
            "w",
            encoding="utf-8",
        ) as f:
            f.write(bodies[-1])

    return bodies


def fetch_latest_bulletin():
    """Backwards-compatible helper: returns only the most recent bulletin's
    body, or None if there isn't one. Prefer fetch_bulletins() for the full
    pipeline, since there can be more than one bulletin in a day."""
    bodies = fetch_bulletins()
    return bodies[-1] if bodies else None


if __name__ == "__main__":
    bulletins = fetch_bulletins()

    if not bulletins:
        print("No new bulletin found with query:", GMAIL_QUERY)
    else:
        print(f"Found {len(bulletins)} bulletin(s). First 500 characters of the first one:\n")
        print(bulletins[0][:500])