"""
Email summarizer — entry point.

Usage:
  python -m backend.main            # start FastAPI (port 8000)
  python -m backend.main --now      # run a digest using smart week logic and exit
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from backend.fetcher import fetch_emails
from backend.summarizer import summarize


OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "digests"))


def _start_of_week() -> datetime:
    """Return Monday 00:00:00 of the current week."""
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    return today - timedelta(days=today.weekday())  # weekday() == 0 on Monday


def _latest_digest_this_week() -> dict | None:
    """
    Return the parsed JSON of the most recent digest from this week, or None.
    Digest filenames are YYYY-MM-DD_HH-MM.json — we filter by the week start date.
    """
    if not OUTPUT_DIR.exists():
        return None

    week_start = _start_of_week()
    candidates = []

    for p in OUTPUT_DIR.glob("*.json"):
        try:
            dt = datetime.strptime(p.stem, "%Y-%m-%d_%H-%M")
            if dt >= week_start:
                candidates.append((dt, p))
        except ValueError:
            continue

    if not candidates:
        return None

    _, latest_path = max(candidates, key=lambda x: x[0])
    return json.loads(latest_path.read_text())


def get_fetch_since() -> datetime:
    """
    Determine the start time for this digest run:
    - If a digest already exists this week, fetch only since its generated_at.
    - Otherwise fetch since Monday 00:00 of the current week.
    """
    latest = _latest_digest_this_week()
    if latest and "generated_at" in latest:
        since = datetime.fromisoformat(latest["generated_at"])
        print(f"[digest] Found existing digest this week — fetching since {since.strftime('%A %b %d %H:%M')}")
        return since

    since = _start_of_week()
    print(f"[digest] No digest yet this week — fetching since {since.strftime('%A %b %d %H:%M')} (start of week)")
    return since


def run_digest(since: datetime | None = None) -> Path:
    """
    Fetch emails since `since` (defaults to smart week logic), summarize, save JSON.
    Returns the output path.
    """
    if since is None:
        since = get_fetch_since()

    print(f"[digest] Fetching emails since {since.isoformat()}...")
    emails = fetch_emails(since=since)
    print(f"[digest] Found {len(emails)} email(s). Summarizing...")

    digest = summarize(emails, since=since)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    out_path = OUTPUT_DIR / f"{timestamp}.json"
    out_path.write_text(json.dumps(digest.model_dump(), indent=2, ensure_ascii=False))

    print(f"[digest] Saved → {out_path}")
    print(f"[digest] {digest.total_emails} emails | {digest.overall_summary[:120]}...")
    return out_path


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Email summarizer")
    parser.add_argument(
        "--now",
        action="store_true",
        help="Run a digest immediately using smart week logic and exit.",
    )
    args = parser.parse_args()

    if args.now:
        run_digest()
    else:
        from backend.api import start as start_api
        start_api(host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
