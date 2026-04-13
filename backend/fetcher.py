"""Gmail fetcher — OAuth2 authentication and email retrieval."""

import base64
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# Paths relative to the project root (one level above backend/)
_ROOT = Path(__file__).parent.parent
TOKEN_PATH = _ROOT / "token.json"
CREDENTIALS_PATH = _ROOT / "credentials.json"

# Maximum body characters to forward to the summarizer per email
_BODY_CHAR_LIMIT = 800


def get_gmail_service():
    """Return an authenticated Gmail API service, running OAuth flow if needed."""
    creds = None

    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_PATH.exists():
                raise FileNotFoundError(
                    f"Gmail OAuth credentials not found at {CREDENTIALS_PATH}.\n"
                    "Download credentials.json from Google Cloud Console → APIs & Services → Credentials."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_PATH), SCOPES
            )
            creds = flow.run_local_server(port=0)

        TOKEN_PATH.write_text(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def fetch_emails(since: datetime) -> list[dict[str, Any]]:
    """
    Fetch emails received since `since`.

    Returns a list of dicts with keys:
        id, sender, subject, received_at, body
    """
    service = get_gmail_service()
    after_epoch = int(since.timestamp())

    results = (
        service.users()
        .messages()
        .list(userId="me", q=f"after:{after_epoch}", maxResults=100)
        .execute()
    )

    message_stubs = results.get("messages", [])
    emails: list[dict[str, Any]] = []

    for stub in message_stubs:
        try:
            msg = (
                service.users()
                .messages()
                .get(userId="me", id=stub["id"], format="full")
                .execute()
            )
            email = _parse_message(msg)
            emails.append(email)
        except Exception as exc:
            print(f"[fetcher] Skipping message {stub['id']}: {exc}")

    return emails


def _parse_message(msg: dict) -> dict[str, Any]:
    """Extract fields from a raw Gmail message object."""
    headers = {h["name"].lower(): h["value"] for h in msg["payload"]["headers"]}

    body = _extract_body(msg["payload"])
    if not body:
        body = msg.get("snippet", "")

    return {
        "id": msg["id"],
        "sender": headers.get("from", ""),
        "subject": headers.get("subject", "(no subject)"),
        "received_at": headers.get("date", ""),
        "body": body[:_BODY_CHAR_LIMIT].strip(),
    }


def _extract_body(payload: dict) -> str:
    """Recursively extract plain-text body from a MIME payload."""
    mime = payload.get("mimeType", "")

    if mime == "text/plain":
        data = payload.get("body", {}).get("data", "")
        if data:
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

    for part in payload.get("parts", []):
        result = _extract_body(part)
        if result:
            return result

    return ""
