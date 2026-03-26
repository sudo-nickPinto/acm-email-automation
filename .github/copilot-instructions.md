# Project: News Digest Email Automation (v4)

## What this project is
A terminal-first tool that sends users a daily email digest of news articles from newspapers they choose. Friends paste one command into their terminal and the installer handles everything — downloading the project, Python installation, newspaper selection, email configuration, and automatic daily scheduling.

## Version history
- **v1 (main branch):** ACM TechNews only, single RSS source, manual `.env` setup
- **v2:** Multi-source newspaper digest, interactive terminal setup, no manual file editing
- **v3:** Adds automatic daily scheduling (macOS LaunchAgent, Linux cron, Windows Task Scheduler). The wizard asks users if they want auto-delivery and at what time.
- **v4 (current, public_attempt branch):** One-line installers (`install.sh` for macOS/Linux, `install.ps1` for Windows) so friends don't need git or a GitHub account. Paste one command → everything works.

## Architecture
```
install.sh            → One-line installer: macOS/Linux (curl | bash)
install.ps1           → One-line installer: Windows (irm | iex)
start.sh              → Bootstrap: installs Python, creates venv, hands off to Python wizard
setup_wizard.py       → Interactive CLI: source selection, email config, scheduling, writes .env
newsdigest/           → Core package
  config.py           → Loads .env, exposes constants (including SCHEDULE_TIME)
  sources.py          → Registry of newspaper RSS feeds with metadata
  scraper.py          → Fetches/parses RSS feeds (multi-source)
  emailer.py          → Formats and sends multi-source digest email
  scheduler.py        → Installs/uninstalls daily schedule (LaunchAgent, cron, Task Scheduler)
  cli.py              → Interactive menu system (launched by `news-digest` with no args)
main.py               → Orchestrator: fetch → deduplicate → send
news-digest           → Global CLI command (bash, symlinked to /usr/local/bin)
tests/                → Test suite (pytest, 150 tests, fully offline)
```

## Key constraints
- **Target audience:** Non-technical users (friends). Zero coding knowledge assumed.
- **Minimal prerequisites:** Only a terminal and a Gmail account. Python install is guided.
- **Terminal-first:** All setup happens interactively in the terminal. No manual file editing.
- **macOS + Linux + Windows:** Must work on all three. `start.sh` detects OS and adjusts. Windows users use PowerShell or Git Bash.
- **Gmail SMTP only:** Uses App Passwords with 2FA. The wizard explains how to get one.
- **Free RSS feeds only:** We can only scrape newspapers that provide public RSS feeds.
- **Scheduling:** macOS uses LaunchAgent plist. Linux uses crontab. Windows uses Task Scheduler (schtasks.exe). The wizard handles installation/removal.

## Code style
- Heavily commented — every function, every block explains *what* and *why*
- Dataclasses over dicts for structured data
- Type hints on all function signatures
- Fail fast, fail loud — no silent exception swallowing
- Single Responsibility — each module has one reason to change

## Documentation
- All docs live in `docs/` and must be kept in sync with code changes
- Numbered files (01-xx.md through 10-xx.md) covering architecture, deep dives, troubleshooting
- README.md at root is the public-facing quickstart

## Commands
- `curl -fsSL <raw-install-url> | bash` — One-line install (macOS/Linux)
- `irm <raw-install-url> | iex` — One-line install (Windows PowerShell)
- `./start.sh` — Full bootstrap + setup wizard (if cloned manually)
- `venv/bin/python3 main.py --dry-run` — Preview without sending
- `venv/bin/python3 main.py` — Send the digest
- `venv/bin/python3 main.py --force` — Bypass duplicate detection
- `news-digest` — Launch interactive menu (send, preview, change settings, uninstall)
- `venv/bin/python3 -m pytest tests/ -v` — Run the test suite (150 tests)
