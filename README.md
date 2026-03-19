## Daily-Git-Commit

Automates small daily commits to keep a GitHub contribution streak. This fork enhances the original project by running a background process on GUI login that makes a randomized number of commits (1–10) spread out with uneven intervals so they appear natural.

## Requirements

- Python 3.8+ (you have Python 3.12.3) — use a virtual environment
- See `requirements.txt` for exact dependency versions

## Setup (one-time)

1. Clone this repository and open it:

```
cd /home/gustavo/Desktop/Daily-Git-Comain
```

2. Create and install into a virtual environment:

```
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

3. Configure Git authentication (required for unattended pushes):

- Recommended: add an SSH key and register the public key on GitHub (preferred for unattended pushes).
- Alternative: create a Personal Access Token (PAT) and use it in an HTTPS remote URL.

4. Verify a manual push works before relying on the autostart runner:

```
.venv/bin/python3 main.py
git push
```

## How it works now

- `main.py` contains the core commit logic: it updates `update_me.yaml` and commits + pushes it.
- `daily_runner.py` (new) is a wrapper that runs on GUI login and:
	- Picks a random number of commits (1–10)
	- Waits an initial random delay (1–5 minutes)
	- Performs commits spaced by random gaps (5–90 minutes)
	- Uses a lock file (`/tmp/daily-git-commit.lock`) so it only runs once per day
	- Logs actions to `~/.local/share/daily-git-commit/log.txt`
- Autostart: the project installs a desktop autostart entry at `~/.config/autostart/daily-git-commit.desktop` that launches the venv Python to run `daily_runner.py` on login.

## Files added or changed

- `daily_runner.py` — scheduler + runner (new)
- `main.py` — minor portability tweak (`os.chdir`) so functions work when invoked from anywhere
- `requirements.txt` — updated dependency versions
- `~/.config/autostart/daily-git-commit.desktop` — autostart entry (created on setup)

## Running / Monitoring

- Manual run (for testing):

```
.venv/bin/python3 daily_runner.py
```

- Monitor activity:

```
tail -f ~/.local/share/daily-git-commit/log.txt
```

## Notes and troubleshooting

- Ensure your SSH key or credentials allow pushing to the repo. SSH is recommended for unattended pushes.
- If the runner exits immediately with "Already ran today", it means the lock file records today's date; remove `/tmp/daily-git-commit.lock` to test again today.
- If `git push` fails from the runner, test pushing manually from the activated venv to diagnose credentials.

## Why?

This project keeps your contribution streaks filled by making small, unobtrusive daily commits. The runner intentionally randomizes count and spacing so activity looks organic rather than scripted.

---

If you want, I can update the README further with screenshots or exact commands for adding SSH keys to GitHub.

