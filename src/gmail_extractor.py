"""
gmail_extractor.py

Connects to Gmail, finds today's UJA bulletin email, and returns its raw
HTML content, ready to be split into activities by bulletin_parser.py.

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


def fetch_latest_bulletin():
    """Finds the most recent bulletin and returns its raw HTML (or plain
    text if the email has no HTML part). Returns None if there's no new
    bulletin. Also saves the HTML to data/latest_bulletin.html."""
    service = get_gmail_service()

    results = (
        service.users()
        .messages()
        .list(userId="me", q=GMAIL_QUERY, maxResults=1)
        .execute()
    )
    messages = results.get("messages", [])

    if not messages:
        return None

    raw_message = (
        service.users()
        .messages()
        .get(userId="me", id=messages[0]["id"], format="raw")
        .execute()
    )
    raw_bytes = base64.urlsafe_b64decode(raw_message["raw"])
    mime_message = message_from_bytes(raw_bytes)

    html, plain = _extract_bodies(mime_message)

    if html:
        os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)
        with open(
            os.path.join(BASE_DIR, "data", "latest_bulletin.html"),
            "w",
            encoding="utf-8",
        ) as f:
            f.write(html)
        return html

    return plain


if __name__ == "__main__":
    content = fetch_latest_bulletin()

    if content is None:
        print("No new bulletin found with query:", GMAIL_QUERY)
    else:
        print("Bulletin extracted successfully. First 500 characters:\n")
        print(content[:500])