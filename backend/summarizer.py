"""Email summarizer — calls the claude CLI to produce a JSON digest."""

import json
import os
import subprocess
from datetime import datetime
from typing import Any

from pydantic import BaseModel


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


class OverallSummary(BaseModel):
    title: str                      # e.g. "3 items require your attention"
    recommendations: list[str]      # one entry per distinct topic/action

    def with_correct_count(self) -> "OverallSummary":
        """Return a copy with the title count matching the actual recommendations length."""
        _words = [
            "zero", "one", "two", "three", "four", "five",
            "six", "seven", "eight", "nine", "ten",
        ]
        n = len(self.recommendations)
        word = _words[n] if n < len(_words) else str(n)
        noun = "item" if n == 1 else "items"
        return self.model_copy(update={"title": f"{word.capitalize()} {noun} require your attention"})


class Digest(BaseModel):
    generated_at: str
    period_from: str
    period_to: str
    total_emails: int
    emails: list[EmailEntry]
    overall_summary: OverallSummary


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """You are an email triage assistant. Your job is to read a batch of emails \
and produce a structured digest.

For each email assign an importance level:
- "high"   — requires attention or action (deadlines, direct asks, urgent issues, anything from a real person that needs a reply)
- "medium" — worth reading but not time-sensitive (FYIs, updates, meeting summaries)
- "low"    — newsletters, marketing, automated notifications, receipts

Write a concise 1–2 sentence summary per email.

For overall_summary:
- "title": a short plain-English headline counting what needs attention, e.g. "3 items require your attention"
- "recommendations": a list of strings, one per distinct topic or action item. Each recommendation should be \
a self-contained sentence describing what to do and why. Group related emails into a single recommendation \
where it makes sense. Ignore low-importance emails unless there is a pattern worth noting. \
Never include a recommendation whose message is that nothing needs to be done. \
Do not reference email numbers or indices (e.g. "email #3") in recommendations.

Respond ONLY with valid JSON matching the schema provided. No markdown fences, no extra text."""


# ---------------------------------------------------------------------------
# Main function
# ---------------------------------------------------------------------------

def summarize(emails: list[dict[str, Any]], since: datetime) -> Digest:
    """
    Send emails to the Claude CLI and return a structured Digest.
    Uses the local Claude Pro subscription — no API key required.
    """
    now = datetime.now()
    period_from = since.isoformat(timespec="seconds")
    period_to = now.isoformat(timespec="seconds")

    if not emails:
        return Digest(
            generated_at=now.isoformat(timespec="seconds"),
            period_from=period_from,
            period_to=period_to,
            total_emails=0,
            emails=[],
            overall_summary=OverallSummary(
                title="No emails this period",
                recommendations=[],
            ),
        )

    full_prompt = (
        f"{_SYSTEM_PROMPT}\n\n"
        f"Today is {now.strftime('%A, %B %d, %Y %H:%M')}.\n"
        f"Summarize the following {len(emails)} email(s) received since "
        f"{since.strftime('%A, %B %d at %H:%M')}.\n\n"
        f"Return JSON with this exact schema:\n"
        f"{_output_schema()}\n\n"
        f"--- EMAILS ---\n{_format_emails(emails)}"
    )

    # Strip ANTHROPIC_API_KEY from the subprocess environment.
    # load_dotenv() sets it in the parent process (even as a blank placeholder),
    # and the Claude CLI inherits it. When present — even empty — the CLI treats
    # it as the auth method and rejects it instead of falling back to the OAuth
    # token stored in the macOS keychain.
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    result = subprocess.run(
        ["/opt/homebrew/bin/claude", "-p", "--no-session-persistence"],
        input=full_prompt,
        capture_output=True,
        text=True,
        timeout=120,
        env=env,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Claude CLI failed (rc={result.returncode})\n"
            f"stdout: {result.stdout.strip()}\n"
            f"stderr: {result.stderr.strip()}"
        )

    raw_json = result.stdout.strip()

    # Strip markdown fences if Claude wrapped the JSON anyway
    if raw_json.startswith("```"):
        raw_json = "\n".join(
            line for line in raw_json.splitlines()
            if not line.startswith("```")
        ).strip()

    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Claude returned invalid JSON: {exc}\n\nRaw output:\n{raw_json}") from exc

    data.setdefault("generated_at", now.isoformat(timespec="seconds"))
    data.setdefault("period_from", period_from)
    data.setdefault("period_to", period_to)
    data.setdefault("total_emails", len(emails))

    digest = Digest.model_validate(data)
    digest.overall_summary = digest.overall_summary.with_correct_count()
    return digest


# ---------------------------------------------------------------------------
# Merge helper
# ---------------------------------------------------------------------------

def update_overall_summary(entries: list[EmailEntry]) -> OverallSummary:
    """
    Generate a new OverallSummary from a list of already-summarized EmailEntry objects.
    Used when merging a new digest into an existing weekly one — avoids re-summarizing
    emails we've already processed, only needs the compact summaries.
    """
    entries_text = "\n".join(
        f"- [{e.importance.upper()}] From: {e.sender} | Subject: {e.subject} | {e.summary}"
        for e in entries
    )

    schema = json.dumps({
        "title": "N items require your attention",
        "recommendations": ["<one action item or topic per entry>"]
    }, indent=2)

    prompt = (
        "You are an email triage assistant.\n\n"
        "Below is a list of emails from this week, each with an importance level and a short summary.\n"
        "Produce an overall_summary with:\n"
        "- \"title\": a short plain-English headline counting what needs attention\n"
        "- \"recommendations\": a list of strings, one per distinct topic or action item.\n"
        "  Group related emails. Ignore low-importance items unless there is a pattern worth noting.\n\n"
        f"Return ONLY valid JSON matching this schema:\n{schema}\n\n"
        f"--- EMAILS ---\n{entries_text}"
    )

    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    result = subprocess.run(
        ["/opt/homebrew/bin/claude", "-p", "--no-session-persistence"],
        input=prompt,
        capture_output=True,
        text=True,
        timeout=60,
        env=env,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Claude CLI failed generating overall summary (rc={result.returncode})\n"
            f"stdout: {result.stdout.strip()}\n"
            f"stderr: {result.stderr.strip()}"
        )

    raw = result.stdout.strip()
    if raw.startswith("```"):
        raw = "\n".join(l for l in raw.splitlines() if not l.startswith("```")).strip()

    return OverallSummary.model_validate(json.loads(raw)).with_correct_count()


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
            "overall_summary": {
                "title": "<short headline, e.g. '3 items require your attention'>",
                "recommendations": ["<one action item or topic per entry>"],
            },
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
