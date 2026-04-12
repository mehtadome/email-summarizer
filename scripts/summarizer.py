"""Email summarizer — calls Claude API to produce a JSON digest."""

import json
from datetime import datetime, timedelta
from typing import Any

import anthropic
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Output schema
# ---------------------------------------------------------------------------

class EmailEntry(BaseModel):
    id: str
    sender: str
    subject: str
    received_at: str
    importance: str  # "high" | "medium" | "low"
    summary: str


class Digest(BaseModel):
    generated_at: str
    period_from: str
    period_to: str
    total_emails: int
    emails: list[EmailEntry]
    overall_summary: str


# ---------------------------------------------------------------------------
# System prompt (cached — never changes between runs)
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """You are an email triage assistant. Your job is to read a batch of emails \
and produce a structured end-of-day digest.

For each email assign an importance level:
- "high"   — requires attention or action today (deadlines, direct asks, urgent issues, anything from a real person that needs a reply)
- "medium" — worth reading but not time-sensitive (FYIs, updates, meeting summaries)
- "low"    — newsletters, marketing, automated notifications, receipts

Write a concise 1–2 sentence summary per email.
Write a brief overall_summary (3–5 sentences) covering the key things that need attention.

Respond ONLY with valid JSON matching the schema provided. No markdown fences, no extra text."""


# ---------------------------------------------------------------------------
# Main function
# ---------------------------------------------------------------------------

def summarize(emails: list[dict[str, Any]], hours_back: int = 24) -> Digest:
    """
    Send emails to Claude and return a structured Digest.

    Uses prompt caching on the system prompt to reduce costs on repeated runs.
    """
    if not emails:
        now = datetime.now()
        return Digest(
            generated_at=now.isoformat(timespec="seconds"),
            period_from=(now - timedelta(hours=hours_back)).isoformat(timespec="seconds"),
            period_to=now.isoformat(timespec="seconds"),
            total_emails=0,
            emails=[],
            overall_summary="No emails received in this period.",
        )

    client = anthropic.Anthropic()

    emails_text = _format_emails(emails)
    now = datetime.now()
    period_from = (now - timedelta(hours=hours_back)).isoformat(timespec="seconds")
    period_to = now.isoformat(timespec="seconds")

    user_content = (
        f"Today is {now.strftime('%A, %B %d, %Y %H:%M')}.\n"
        f"Summarize the following {len(emails)} email(s) received in the last {hours_back} hours.\n\n"
        f"Return JSON with this exact schema:\n"
        f"{_output_schema()}\n\n"
        f"--- EMAILS ---\n{emails_text}"
    )

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=4096,
        system=[
            {
                "type": "text",
                "text": _SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": user_content}],
    )

    raw_json = next(b.text for b in response.content if b.type == "text")

    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Claude returned invalid JSON: {exc}\n\nRaw output:\n{raw_json}") from exc

    # Inject period metadata (Claude doesn't know the exact ISO timestamps)
    data.setdefault("generated_at", now.isoformat(timespec="seconds"))
    data.setdefault("period_from", period_from)
    data.setdefault("period_to", period_to)
    data.setdefault("total_emails", len(emails))

    return Digest.model_validate(data)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _format_emails(emails: list[dict]) -> str:
    parts = []
    for i, e in enumerate(emails, 1):
        parts.append(
            f"[{i}] ID: {e['id']}\n"
            f"    From: {e['sender']}\n"
            f"    Subject: {e['subject']}\n"
            f"    Date: {e['received_at']}\n"
            f"    Body: {e['body']}"
        )
    return "\n\n".join(parts)


def _output_schema() -> str:
    return json.dumps(
        {
            "generated_at": "<ISO timestamp>",
            "period_from": "<ISO timestamp>",
            "period_to": "<ISO timestamp>",
            "total_emails": "<int>",
            "overall_summary": "<string>",
            "emails": [
                {
                    "id": "<string>",
                    "sender": "<string>",
                    "subject": "<string>",
                    "received_at": "<string>",
                    "importance": "<high|medium|low>",
                    "summary": "<string>",
                }
            ],
        },
        indent=2,
    )
