"""
gmail_extractor.py

Connects to Gmail, finds today's UJA bulletin email, and returns its content
as clean text, ready to be passed to the AI filter.

Usage:
    python src/gmail_extractor.py
"""

import base64
import os

from bs4 import BeautifulSoup
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


def _get_html_from_payload(payload):
    """Walks the whole message payload (which can have several nested parts,
    e.g. a text/plain version AND a text/html version side by side) and
    returns the HTML version if one exists ANYWHERE in the tree, falling
    back to plain text only if no HTML part was found at all."""
    html, plain = _collect_bodies(payload)

    if html:
        return html, "html"
    if plain:
        return plain, "plain"
    return None


def _collect_bodies(payload):
    """Recursively gathers the first html and first plain text bodies found
    anywhere in the payload tree, regardless of the order the parts appear in."""
    html = None
    plain = None

    mime = payload.get("mimeType", "")
    body = payload.get("body", {})

    if mime == "text/html" and "data" in body:
        html = _decode(body["data"])
    elif mime == "text/plain" and "data" in body:
        plain = _decode(body["data"])

    for part in payload.get("parts", []):
        child_html, child_plain = _collect_bodies(part)
        html = html or child_html
        plain = plain or child_plain

    return html, plain


def _decode(data):
    return base64.urlsafe_b64decode(data.encode("ASCII")).decode("utf-8", errors="ignore")


def fetch_latest_bulletin():
    """Finds the most recent bulletin and returns its clean text (no HTML tags).
    Returns None if there's no new bulletin."""
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

    msg = (
        service.users()
        .messages()
        .get(userId="me", id=messages[0]["id"], format="full")
        .execute()
    )

    content, content_type = _get_html_from_payload(msg["payload"])

    if content_type == "html":
        # Save the original HTML in case you want to fine-tune the extractor later
        os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)
        with open(os.path.join(BASE_DIR, "data", "latest_bulletin.html"), "w") as f:
            f.write(content)

        soup = BeautifulSoup(content, "html.parser")
        text = soup.get_text(separator="\n", strip=True)
    else:
        text = content

    return text


if __name__ == "__main__":
    text = fetch_latest_bulletin()

    if text is None:
        print("No new bulletin found with query:", GMAIL_QUERY)
    else:
        print("Bulletin extracted successfully. First 500 characters:\n")
        print(text[:500])