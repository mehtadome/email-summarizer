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
from backend.summarizer import summarize, update_overall_summary, EmailEntry, Digest


OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "digests"))


def _start_of_week() -> datetime:
    """Return Monday 00:00:00 of the current week."""
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    return today - timedelta(days=today.weekday())  # weekday() == 0 on Monday


def _latest_weekly_digest() -> tuple[Path, dict] | tuple[None, None]:
    """
    Return (path, parsed_json) of the most recent digest from this week, or (None, None).
    Digest filenames are YYYY-MM-DD_HH-MM.json — filtered by the current week start.
    """
    if not OUTPUT_DIR.exists():
        return None, None

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
        return None, None

    _, latest_path = max(candidates, key=lambda x: x[0])
    return latest_path, json.loads(latest_path.read_text())


def get_fetch_since() -> datetime:
    """
    Determine the start time for this digest run:
    - If a digest already exists this week, fetch only since its generated_at.
    - Otherwise fetch since Monday 00:00 of the current week.
    """
    _, latest = _latest_weekly_digest()
    if latest and "generated_at" in latest:
        since = datetime.fromisoformat(latest["generated_at"])
        print(f"[digest] Found existing digest this week — fetching since {since.strftime('%A %b %d %H:%M')}")
        return since

    since = _start_of_week()
    print(f"[digest] No digest yet this week — fetching since {since.strftime('%A %b %d %H:%M')} (start of week)")
    return since


def run_digest(since: datetime | None = None) -> Path:
    """
    Fetch emails, merge with existing weekly digest if one exists, save as single file.

    - First pull of the week: fetches since Monday 00:00, saves fresh digest.
    - Subsequent pulls: fetches only new emails, merges with existing weekly digest,
      deletes the old file, saves a new file named with the current timestamp.
    """
    now = datetime.now()

    if since is None:
        since = get_fetch_since()

    print(f"[digest] Fetching emails since {since.isoformat()}...")
    new_emails = fetch_emails(since=since)
    print(f"[digest] Found {len(new_emails)} new email(s).")

    existing_path, existing_data = _latest_weekly_digest()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = now.strftime("%Y-%m-%d_%H-%M")
    out_path = OUTPUT_DIR / f"{timestamp}.json"

    if existing_path and not new_emails:
        # Nothing new — return the existing file as-is
        print("[digest] No new emails since last digest.")
        return existing_path

    if existing_path and new_emails:
        # Summarize only the new emails
        print(f"[digest] Summarizing {len(new_emails)} new email(s)...")
        new_digest = summarize(new_emails, since=since)

        # Merge old entries + new entries
        existing_entries = [EmailEntry(**e) for e in existing_data["emails"]]
        all_entries = existing_entries + new_digest.emails
        print(f"[digest] Merging {len(existing_entries)} existing + {len(new_digest.emails)} new entries...")

        # Regenerate overall summary across the full week
        overall = update_overall_summary(all_entries)

        merged = Digest(
            generated_at=now.isoformat(timespec="seconds"),
            period_from=existing_data["period_from"],  # keep original week-start
            period_to=now.isoformat(timespec="seconds"),
            total_emails=len(all_entries),
            emails=all_entries,
            overall_summary=overall,
        )

        # Replace old file with merged file
        existing_path.unlink()
        out_path.write_text(json.dumps(merged.model_dump(), indent=2, ensure_ascii=False))
        print(f"[digest] Merged digest saved → {out_path} ({merged.total_emails} total emails)")
        return out_path

    # No existing digest this week — fresh run
    print(f"[digest] Summarizing {len(new_emails)} email(s)...")
    digest = summarize(new_emails, since=since)
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
