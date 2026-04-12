"""APScheduler setup — runs the daily digest job at 5 PM."""

import os
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from apscheduler.schedulers.blocking import BlockingScheduler


def _get_timezone():
    tz_name = os.getenv("TIMEZONE", "").strip()
    if tz_name:
        try:
            return ZoneInfo(tz_name)
        except ZoneInfoNotFoundError:
            print(f"[scheduler] Unknown timezone '{tz_name}', falling back to local time.")
    return None  # None = local system time


def start(job_fn):
    """
    Start the blocking scheduler.

    `job_fn` is called every day at 17:00 local time (or TIMEZONE if set).
    This call blocks until the process is interrupted.
    """
    tz = _get_timezone()
    scheduler = BlockingScheduler(timezone=tz)

    scheduler.add_job(
        job_fn,
        trigger="cron",
        hour=17,
        minute=0,
        id="daily_digest",
        name="Daily email digest",
        misfire_grace_time=300,  # tolerate up to 5 min late start
    )

    tz_label = str(tz) if tz else "local system time"
    print(f"[scheduler] Digest scheduled for 17:00 {tz_label} — waiting...")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("[scheduler] Stopped.")
