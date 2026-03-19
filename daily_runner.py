"""
daily_runner.py — runs on login, makes 1–10 commits staggered with
uneven random intervals so they don't look scripted.
"""

import os
import random
import time
import logging
from datetime import date
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
REPO_DIR = Path(__file__).parent.resolve()
LOCK_FILE = Path('/tmp/daily-git-commit.lock')
LOG_DIR   = Path.home() / '.local' / 'share' / 'daily-git-commit'
LOG_FILE  = LOG_DIR / 'log.txt'

# ── Logging ────────────────────────────────────────────────────────────────────
LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s  %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(),
    ]
)
log = logging.getLogger(__name__)


def already_ran_today() -> bool:
    """Return True if we've already completed a run today (lock file contains today's date)."""
    if LOCK_FILE.exists():
        try:
            stored = LOCK_FILE.read_text().strip()
            return stored == str(date.today())
        except OSError:
            pass
    return False


def mark_ran_today():
    """Write today's date into the lock file."""
    LOCK_FILE.write_text(str(date.today()))


def random_intervals(n: int) -> list[int]:
    """
    Return a list of n sleep durations (seconds) that are uneven.
    First element is the initial delay before the very first commit.
    The rest are gaps between subsequent commits.

    Ranges used:
      - initial delay : 60 – 300 s  (1 – 5 min)
      - between commits: 300 – 5400 s  (5 – 90 min)
    """
    delays = [random.randint(60, 300)]          # initial delay
    delays += [random.randint(300, 5400) for _ in range(n - 1)]
    return delays


def main():
    os.chdir(REPO_DIR)

    if already_ran_today():
        log.info("Already ran today — exiting.")
        return

    # Import here so the venv path is already active at this point
    from main import update_file_to_commit, commit_repository

    commit_count = random.randint(1, 10)
    intervals    = random_intervals(commit_count)

    log.info(f"Session start — planning {commit_count} commit(s) today.")
    log.info(f"Intervals (seconds): {intervals}")

    for i in range(commit_count):
        sleep_secs = intervals[i]
        label = "Initial delay" if i == 0 else f"Gap before commit {i + 1}"
        log.info(f"{label}: sleeping {sleep_secs}s ({sleep_secs // 60}m {sleep_secs % 60}s)...")
        time.sleep(sleep_secs)

        try:
            yaml_data = update_file_to_commit()
            commit_repository(yaml_data)
            log.info(f"Commit {i + 1}/{commit_count} done — update #{yaml_data['UPDATE_TIMES']}")
        except Exception as exc:
            log.error(f"Commit {i + 1} failed: {exc}")

    mark_ran_today()
    log.info("All commits complete for today.")


if __name__ == '__main__':
    main()
