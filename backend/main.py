"""
Email summarizer — entry point.

Usage:
  python -m backend.main            # start FastAPI (port 8000)
  python -m backend.main --now      # run a digest and exit
"""

import json
import os
from datetime import datetime, timedelta
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


def run_digest(since: datetime | None = None) -> Path | None:
    """
    Fetch emails since the last run, summarize, and persist.

    Same-day logic: if a digest file for today already exists, new emails are
    appended and recommendations are concatenated (no re-inference on existing
    emails). generated_at is updated so subsequent runs pick up from here.

    New day: creates a fresh file named with the current timestamp.
    """
    now = datetime.now()

    if since is None:
        since = get_fetch_since()

    print(f"[digest] Fetching emails since {since.isoformat()}...")
    new_emails = fetch_emails(since=since)
    print(f"[digest] Found {len(new_emails)} new email(s).")

    today_path, today_data = _today_digest()

    if not new_emails:
        print("[digest] No new emails since last digest.")
        return today_path or _latest_digest()[0]

    print(f"[digest] Summarizing {len(new_emails)} email(s)...")
    new_digest = summarize(new_emails, since=since)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if today_path and today_data:
        # Same-day merge: append emails and recommendations, recompute title.
        existing_entries = [EmailEntry(**{**e, "account": e.get("account", "")}) for e in today_data["emails"]]
        all_entries = existing_entries + new_digest.emails

        existing_recs = today_data.get("overall_summary", {}).get("recommendations", [])
        merged_overall = OverallSummary(
            title="",
            recommendations=existing_recs + new_digest.overall_summary.recommendations,
        ).with_correct_count()

        merged = Digest(
            generated_at=now.isoformat(timespec="seconds"),
            period_from=today_data["period_from"],
            period_to=now.isoformat(timespec="seconds"),
            total_emails=len(all_entries),
            emails=all_entries,
            overall_summary=merged_overall,
        )

        today_path.write_text(json.dumps(merged.model_dump(), indent=2, ensure_ascii=False))
        print(f"[digest] Merged into today's digest → {today_path} ({merged.total_emails} total emails)")
        return today_path

    # First run of the day — new file.
    out_path = OUTPUT_DIR / f"{now.strftime('%Y-%m-%d_%H-%M')}.json"
    out_path.write_text(json.dumps(new_digest.model_dump(), indent=2, ensure_ascii=False))
    print(f"[digest] Saved → {out_path}")
    print(f"[digest] {new_digest.total_emails} emails | {new_digest.overall_summary.title}...")
    return out_path


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
