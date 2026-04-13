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

from dotenv import load_dotenv

load_dotenv()

from backend.fetcher import fetch_emails
from backend.summarizer import summarize, Digest


OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "digests"))


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
    Determine the start time for this digest run:
    - If a previous digest exists, fetch only since its generated_at.
    - Otherwise fall back to 7 days ago.
    """
    _, latest = _latest_digest()
    if latest and "generated_at" in latest:
        since = datetime.fromisoformat(latest["generated_at"])
        print(f"[digest] Found existing digest — fetching since {since.strftime('%A %b %d %H:%M')}")
        return since

    since = datetime.now() - timedelta(days=7)
    print(f"[digest] No existing digest — fetching last 7 days since {since.strftime('%A %b %d %H:%M')}")
    return since


def run_digest(since: datetime | None = None) -> Path | None:
    """
    Fetch emails since the last digest (or 7 days ago if none), summarize, save as new file.
    Each run produces its own file; no merging or overwriting of previous digests.
    """
    now = datetime.now()

    if since is None:
        since = get_fetch_since()

    print(f"[digest] Fetching emails since {since.isoformat()}...")
    new_emails = fetch_emails(since=since)
    print(f"[digest] Found {len(new_emails)} new email(s).")

    if not new_emails:
        print("[digest] No new emails since last digest.")
        latest_path, _ = _latest_digest()
        return latest_path

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = now.strftime("%Y-%m-%d_%H-%M")
    out_path = OUTPUT_DIR / f"{timestamp}.json"

    print(f"[digest] Summarizing {len(new_emails)} email(s)...")
    digest = summarize(new_emails, since=since)
    out_path.write_text(json.dumps(digest.model_dump(), indent=2, ensure_ascii=False))
    print(f"[digest] Saved → {out_path}")
    print(f"[digest] {digest.total_emails} emails | {digest.overall_summary.title}...")
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
