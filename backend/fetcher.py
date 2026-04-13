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
CREDENTIALS_PATH = _ROOT / "credentials.json"

# Maximum body characters to forward to the summarizer per email
_BODY_CHAR_LIMIT = 800


def _token_path(account: str) -> Path:
    """Return the token file path for a given account email."""
    # Primary account uses the legacy token.json for backwards compatibility.
    primary = os.getenv("GMAIL_ACCOUNTS", "").split(",")[0].strip()
    if account == primary or not primary:
        return _ROOT / "token.json"
    safe = account.replace("@", "_").replace(".", "_")
    return _ROOT / f"token_{safe}.json"


def get_gmail_service(account: str):
    """Return an authenticated Gmail API service for the given account."""
    token_path = _token_path(account)
    creds = None

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

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

        token_path.write_text(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def fetch_emails(since: datetime) -> list[dict[str, Any]]:
    """
    Fetch emails received since `since` across all configured accounts.

    Accounts are read from the GMAIL_ACCOUNTS env var (comma-separated).
    Each email is tagged with the account it was fetched from.

    Returns a list of dicts with keys:
        id, account, sender, subject, received_at, body
    """
    raw_accounts = os.getenv("GMAIL_ACCOUNTS", "")
    accounts = [a.strip() for a in raw_accounts.split(",") if a.strip()]

    if not accounts:
        raise ValueError(
            "GMAIL_ACCOUNTS is not set. Add it to your .env file, e.g.:\n"
            "GMAIL_ACCOUNTS=you@gmail.com,other@gmail.com"
        )

    all_emails: list[dict[str, Any]] = []
    for account in accounts:
        print(f"[fetcher] Fetching for {account}...")
        emails = _fetch_for_account(account, since)
        print(f"[fetcher] Found {len(emails)} email(s) for {account}.")
        all_emails.extend(emails)

    return all_emails


def _fetch_for_account(account: str, since: datetime) -> list[dict[str, Any]]:
    """Fetch emails for a single account and tag each with the account address."""
    service = get_gmail_service(account)
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
            email = _parse_message(msg, account)
            emails.append(email)
        except Exception as exc:
            print(f"[fetcher] Skipping message {stub['id']}: {exc}")

    return emails


def _parse_message(msg: dict, account: str) -> dict[str, Any]:
    """Extract fields from a raw Gmail message object."""
    headers = {h["name"].lower(): h["value"] for h in msg["payload"]["headers"]}

    body = _extract_body(msg["payload"])
    if not body:
        body = msg.get("snippet", "")

    return {
        "id": msg["id"],
        "account": account,
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
