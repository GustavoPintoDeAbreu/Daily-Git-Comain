# Daily-Git-Comain

Automates small daily commits to keep a GitHub contribution streak alive. A background
process starts on GUI login, makes a randomized number of commits (1–10), and spaces
them out with uneven intervals.

Each commit bumps a counter in `update_me.yaml` and pushes it. There is no other content
change — the repository exists to produce contribution activity.

## Requirements

- **Python 3.9+** — `daily_runner.py` uses a builtin-generic annotation (`list[int]`),
  which is a `TypeError` on 3.8. Currently running Python 3.12.3.
- A virtual environment at `.venv/` in the repo root.
- SSH authentication to GitHub. Unattended pushes cannot answer a password prompt, so
  HTTPS-with-password will not work; use an SSH key or a PAT baked into the remote URL.
- A desktop session that honours XDG autostart (GNOME, KDE, XFCE, …). Verified on
  Ubuntu GNOME / X11.

## How it works

Four layers, each of which must succeed for a commit to happen:

```
GNOME session start
  └─ ~/.config/autostart/daily-git-commit.desktop     autostart entry
       └─ ~/.local/bin/daily-git-commit.sh            launcher (mkdir, cd, exec)
            └─ daily_runner.py                       scheduling + staggering
                 └─ main.py                          bump counter, commit, push
```

**`main.py`** — the core commit logic. Reads `update_me.yaml`, increments
`UPDATE_TIMES`, stamps `LAST_UPDATE`, writes it back, then commits and pushes.
Runnable on its own for a single immediate commit.

**`daily_runner.py`** — decides *when* commits happen:

- picks a random commit count (1–10) for the day
- waits a random initial delay (60–300s) before the first commit
- spaces subsequent commits by random gaps (300–5400s, i.e. 5–90 min)
- records the date in `/tmp/daily-git-commit.lock` so it runs at most once per day
- logs to `~/.local/share/daily-git-commit/log.txt`

A full day's schedule can span **up to ~8 hours**. Only the first commit matters for the
streak; the rest are padding.

**`daily-git-commit.sh`** — creates the log directory, changes into the repo, and execs
the venv Python. This exists so the `.desktop` `Exec` line stays free of characters the
Desktop Entry spec reserves (`'`, `&`, `>`). See *Troubleshooting*.

## Setup from scratch

1. Clone and enter the repo:

   ```bash
   git clone git@github.com:GustavoPintoDeAbreu/Daily-Git-Comain.git
   cd Daily-Git-Comain
   ```

2. Create the virtualenv and install dependencies:

   ```bash
   python3 -m venv .venv
   .venv/bin/pip install -r requirements.txt
   ```

3. Confirm SSH auth and that a manual commit pushes cleanly:

   ```bash
   ssh -T git@github.com          # expect "successfully authenticated"
   .venv/bin/python3 main.py
   git log -1 && git status       # expect a new commit, clean tree
   ```

4. Create the launcher at `~/.local/bin/daily-git-commit.sh`:

   ```bash
   #!/bin/bash
   REPO_DIR="$HOME/Desktop/Daily-Git-Comain"
   LOG_DIR="$HOME/.local/share/daily-git-commit"

   mkdir -p "$LOG_DIR" || exit 1
   cd "$REPO_DIR" || exit 1

   exec .venv/bin/python3 daily_runner.py >> "$LOG_DIR/log.txt" 2>&1
   ```

   Then `chmod +x ~/.local/bin/daily-git-commit.sh`.

5. Create the autostart entry at `~/.config/autostart/daily-git-commit.desktop`:

   ```ini
   [Desktop Entry]
   Type=Application
   Name=Daily Git Commit
   Comment=Runs background script that makes 1-10 staggered git commits each login
   Exec=/home/gustavo/.local/bin/daily-git-commit.sh
   X-GNOME-Autostart-enabled=true
   NoDisplay=true
   ```

   `Exec` must be an absolute path — `~` and `$HOME` are not expanded in a `.desktop`
   file.

6. Validate the entry and dry-run the launcher:

   ```bash
   desktop-file-validate ~/.config/autostart/daily-git-commit.desktop   # silent = valid
   rm -f /tmp/daily-git-commit.lock
   ~/.local/bin/daily-git-commit.sh &
   tail -f ~/.local/share/daily-git-commit/log.txt
   ```

## Files

| Path | Role |
| --- | --- |
| `main.py` | Counter bump + commit + push |
| `daily_runner.py` | Commit count, delays, once-per-day lock, logging |
| `update_me.yaml` | The committed payload (`UPDATE_TIMES`, `LAST_UPDATE`) |
| `requirements.txt` | GitPython, PyYAML (pinned) |
| `run.bat` | **Vestigial.** Windows launcher from the upstream fork, still hardcoded to the original author's paths. Unused on Linux. |
| `~/.local/bin/daily-git-commit.sh` | Launcher — outside the repo |
| `~/.config/autostart/daily-git-commit.desktop` | Autostart entry — outside the repo |
| `~/.local/share/daily-git-commit/log.txt` | Runtime log — outside the repo |
| `/tmp/daily-git-commit.lock` | Once-per-day marker — cleared on reboot |

## Monitoring

```bash
tail -f ~/.local/share/daily-git-commit/log.txt   # live activity
cat /tmp/daily-git-commit.lock                    # date of last completed run
pgrep -af daily_runner.py                         # is a run in progress?
git log --oneline -5                              # recent commits
```

A healthy login produces `Session start — planning N commit(s) today.` within a second,
then the first commit 1–5 minutes later.

## Troubleshooting

**Nothing happens at login, and the log file is empty or absent.**
Run the launcher by hand — `~/.local/bin/daily-git-commit.sh` — and read the error. Two
failure modes have bitten this setup before, both silent:

- *Missing log directory.* If the launcher redirects into a directory that does not
  exist, bash opens the `>>` redirect **before** running the command, so it dies at the
  redirect and Python never starts. `daily_runner.py` creates that directory itself, but
  never gets the chance. The `mkdir -p` in the launcher exists for this reason.
- *Reserved characters in `Exec`.* `'`, `&`, and `>` are reserved in Desktop Entry
  values. An `Exec` line containing an inline shell pipeline may be rejected. Keep the
  shell logic in the launcher script and check with `desktop-file-validate`.

A trailing `&` in `Exec` makes the shell exit 0 regardless, so both of these fail
*silently* — the session manager sees success. Trust the log, not the exit code.

**"Already ran today — exiting."**
The lock records today's date. `rm -f /tmp/daily-git-commit.lock` to force another run.

**Commits are made but never reach GitHub.**
Test the push path directly: `.venv/bin/python3 main.py` then `git status`. If it reports
commits ahead of `origin/master`, the push is failing — check `ssh -T git@github.com`.

**Counter drifts or `update_me.yaml` conflicts.**
The counter is only meaningful locally. If the file conflicts, take either side and
continue; nothing depends on the exact value.

## Known limitations

- **Login-triggered only.** No login on a given day means no commits that day. A systemd
  user timer with `Persistent=true` would fire regardless and catch up after downtime.
- **A failed day is still marked done.** `mark_ran_today()` runs after the commit loop
  regardless of outcome, and per-commit exceptions are caught and logged. If every commit
  fails, the day is recorded as complete and will not retry.
- **Long runs are fragile.** A schedule spanning hours is lost if the machine sleeps or
  shuts down mid-run; the lock is never written, so the next login restarts the day.
- **Doubled log lines.** `logging` writes to both a `FileHandler` and a `StreamHandler`,
  and the launcher redirects stderr into the same file. Cosmetic; drop one of the two.

## Why?

It keeps the contribution graph filled. Worth being clear-eyed about what that means:
the graph reads to others as evidence of real work, and the randomized timing is there
specifically so the activity does not look automated. That is the actual purpose of the
staggering — not a technical requirement.
