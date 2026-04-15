"""
Email summarizer — entry point.

Usage:
  python -m backend.main            # start FastAPI (port 8000)
  python -m backend.main --now      # run a digest and exit
"""

import json
import os
from datetime import datetime, timedelta, date
from email.utils import parsedate_to_datetime as _parse_rfc2822
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

load_dotenv()

from backend.fetcher import fetch_emails
from backend.summarizer import summarize, EmailEntry, Digest, OverallSummary


OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "digests"))

# Day boundary is 12:00am–11:59pm in the configured timezone.
# NOTE: emails arriving in the 1-minute window around midnight may land in the
# wrong day's file. Accepted tradeoff for simplicity.
_TZ = ZoneInfo(os.getenv("TIMEZONE", "America/Los_Angeles"))


def _today_digest() -> tuple[Path, dict] | tuple[None, None]:
    """
    Return (path, parsed_json) for today's digest file (matched by local date prefix),
    or (None, None) if no file exists for today yet.
    """
    if not OUTPUT_DIR.exists():
        return None, None

    today_str = datetime.now(_TZ).strftime("%Y-%m-%d")
    candidates = []

    for p in OUTPUT_DIR.glob(f"{today_str}_*.json"):
        try:
            dt = datetime.strptime(p.stem, "%Y-%m-%d_%H-%M")
            candidates.append((dt, p))
        except ValueError:
            continue

    if not candidates:
        return None, None

    _, path = max(candidates, key=lambda x: x[0])
    return path, json.loads(path.read_text())


def _latest_digest() -> tuple[Path, dict] | tuple[None, None]:
    """Return (path, parsed_json) of the most recent digest on disk, or (None, None)."""
    if not OUTPUT_DIR.exists():
        return None, None

    candidates = []
    for p in OUTPUT_DIR.glob("*.json"):
        try:
            dt = datetime.strptime(p.stem, "%Y-%m-%d_%H-%M")
            candidates.append((dt, p))
        except ValueError:
            continue

    if not candidates:
        return None, None

    _, latest_path = max(candidates, key=lambda x: x[0])
    return latest_path, json.loads(latest_path.read_text())


def get_fetch_since() -> datetime:
    """
    Determine the start time for this digest run.
    Reads generated_at from today's file if one exists, otherwise from the
    most recent file on disk. Falls back to 7 days ago on first ever run.
    """
    for label, (_, data) in [
        ("today's digest", _today_digest()),
        ("latest digest", _latest_digest()),
    ]:
        if data and "generated_at" in data:
            since = datetime.fromisoformat(data["generated_at"])
            print(f"[digest] Found {label} — fetching since {since.strftime('%A %b %d %H:%M')}")
            return since

    since = datetime.now() - timedelta(days=7)
    print(f"[digest] No existing digest — fetching last 7 days since {since.strftime('%A %b %d %H:%M')}")
    return since


def _received_date(email: dict) -> date | None:
    """Parse an email's received_at (RFC 2822) and return the local date, or None."""
    try:
        return _parse_rfc2822(email["received_at"]).astimezone(_TZ).date()
    except Exception:
        return None


def _split_by_today(emails: list[dict], today: date) -> tuple[list[dict], list[dict]]:
    """
    Split emails into (prev_day, today) buckets.
    Emails that can't be parsed default to today's bucket.
    """
    prev, today_emails = [], []
    for e in emails:
        d = _received_date(e)
        if d is not None and d < today:
            prev.append(e)
        else:
            today_emails.append(e)
    return prev, today_emails


def _merge_into_file(path: Path, data: dict, new_entries: list[EmailEntry],
                     new_recs: list[str], write_time: datetime) -> None:
    """Append new email entries and recommendations into an existing digest file."""
    existing_entries = [
        EmailEntry(**{**e, "account": e.get("account", ""), "thread_id": e.get("thread_id", "")})
        for e in data["emails"]
    ]
    all_entries = existing_entries + new_entries
    existing_recs = data.get("overall_summary", {}).get("recommendations", [])
    merged_overall = OverallSummary(
        title="",
        recommendations=existing_recs + new_recs,
    ).with_correct_count()
    merged = Digest(
        generated_at=write_time.isoformat(timespec="seconds"),
        period_from=data["period_from"],
        period_to=write_time.isoformat(timespec="seconds"),
        total_emails=len(all_entries),
        emails=all_entries,
        overall_summary=merged_overall,
    )
    path.write_text(json.dumps(merged.model_dump(), indent=2, ensure_ascii=False))


def run_digest(since: datetime | None = None) -> Path | None:
    """
    Fetch emails since the last run, summarize, and persist.

    Same-day: appends new emails and recommendations into today's file.

    First run of the day: splits fetched emails by received date.
      - Emails from previous day(s) are summarized and merged into the previous
        day's file. Their recommendations are carried over to today's digest
        prefixed with a date tag (e.g. "[Apr 14]") so they surface in today's view.
      - Emails received today go into a new file for today.
    """
    run_start = datetime.now()

    if since is None:
        since = get_fetch_since()

    print(f"[digest] Fetching emails since {since.isoformat()}...")
    new_emails = fetch_emails(since=since)
    print(f"[digest] Found {len(new_emails)} new email(s).")

    today_path, today_data = _today_digest()

    if not new_emails:
        print("[digest] No new emails since last digest.")
        return today_path or _latest_digest()[0]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if today_path and today_data:
        # Same-day merge: append emails and recommendations, recompute title.
        print(f"[digest] Summarizing {len(new_emails)} new email(s)...")
        new_digest = summarize(new_emails, since=since)
        write_time = datetime.now()

        existing_entries = [
            EmailEntry(**{**e, "account": e.get("account", ""), "thread_id": e.get("thread_id", "")})
            for e in today_data["emails"]
        ]
        all_entries = existing_entries + new_digest.emails
        existing_recs = today_data.get("overall_summary", {}).get("recommendations", [])
        merged_overall = OverallSummary(
            title="",
            recommendations=existing_recs + new_digest.overall_summary.recommendations,
        ).with_correct_count()
        merged = Digest(
            generated_at=write_time.isoformat(timespec="seconds"),
            period_from=today_data["period_from"],
            period_to=write_time.isoformat(timespec="seconds"),
            total_emails=len(all_entries),
            emails=all_entries,
            overall_summary=merged_overall,
        )
        today_path.write_text(json.dumps(merged.model_dump(), indent=2, ensure_ascii=False))
        print(f"[digest] Merged into today's digest → {today_path} ({merged.total_emails} total emails)")
        return today_path

    # First run of the day — split emails by received date.
    today_date = datetime.now(_TZ).date()
    prev_emails, todays_emails = _split_by_today(new_emails, today_date)

    carried_recs: list[str] = []

    if prev_emails:
        print(f"[digest] {len(prev_emails)} email(s) from previous day — summarizing into yesterday's file...")
        prev_digest = summarize(prev_emails, since=since)
        write_time = datetime.now()

        prev_path, prev_data = _latest_digest()
        if prev_path and prev_data:
            _merge_into_file(prev_path, prev_data, prev_digest.emails,
                             prev_digest.overall_summary.recommendations, write_time)
            print(f"[digest] Updated previous day's digest → {prev_path}")

        # Tag recommendations for carry-over into today's view.
        prev_date = today_date - timedelta(days=1)
        tag = f"[{prev_date.strftime('%b')} {prev_date.day}]"
        carried_recs = [f"{tag} {r}" for r in prev_digest.overall_summary.recommendations]

    if todays_emails:
        print(f"[digest] Summarizing {len(todays_emails)} email(s) for today...")
        today_midnight = datetime.now(_TZ).replace(
            hour=0, minute=0, second=0, microsecond=0
        ).replace(tzinfo=None)
        today_digest = summarize(todays_emails, since=today_midnight)
        write_time = datetime.now()

        if carried_recs:
            today_digest.overall_summary = OverallSummary(
                title="",
                recommendations=carried_recs + today_digest.overall_summary.recommendations,
            ).with_correct_count()

        today_digest.generated_at = write_time.isoformat(timespec="seconds")
        today_digest.period_to = write_time.isoformat(timespec="seconds")
        out_path = OUTPUT_DIR / f"{run_start.strftime('%Y-%m-%d_%H-%M')}.json"
        out_path.write_text(json.dumps(today_digest.model_dump(), indent=2, ensure_ascii=False))
        print(f"[digest] Saved → {out_path}")
        print(f"[digest] {today_digest.total_emails} emails | {today_digest.overall_summary.title}...")
        return out_path

    # Only previous-day emails, no emails received today.
    prev_path, _ = _latest_digest()
    return prev_path


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Email summarizer")
    parser.add_argument(
        "--now",
        action="store_true",
        help="Run a digest immediately and exit.",
    )
    args = parser.parse_args()

    if args.now:
        run_digest()
    else:
        from backend.api import start as start_api
        start_api(host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
