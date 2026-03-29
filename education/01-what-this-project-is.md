# Lesson 01 — What This Project Is

## The problem

You want to stay current on technology news, but visiting multiple newspaper websites every morning is tedious. RSS readers exist, but many of your friends find them confusing. What if you could receive a single, clean email every morning with the top articles from the newspapers you care about — and what if setting it up was as simple as pasting one command into your terminal?

## The solution

News Digest is a command-line tool that:

1. **Fetches** articles from newspaper RSS feeds you select (ACM TechNews, MIT Technology Review, New York Times Technology, BBC Technology)
2. **Filters** to only today's articles so you never see stale news
3. **Formats** them into a clean, styled email with sections per newspaper
4. **Sends** the email to your Gmail inbox via SMTP
5. **Schedules** itself to run automatically every day at a time you choose

The user experience is: paste one command, answer a few questions, get daily news emails forever (or until you uninstall).

## Target audience

The target users for this tool are **non-technical friends**. This is the single most important design constraint in the entire project. Every decision — from using Gmail (which everyone already has) to wrapping everything in an interactive wizard — stems from this constraint.

Specifically, this means:
- **Zero coding knowledge assumed** — users never edit a file, write a command from memory, or understand what Python is
- **Terminal-first** — all interaction happens in the terminal, but the terminal prompts are as friendly as a GUI
- **Guided experience** — every prompt explains what it is asking and why, with examples
- **Recoverable mistakes** — users can re-run the wizard, change settings through the menu, or uninstall cleanly

## Version history

The project evolved through four major versions, each building on the last:

### v1 — Single source, manual setup
- Only fetched ACM TechNews (one RSS feed)
- Required users to manually create and edit a `.env` file
- No scheduling — users had to run a command each time
- Lived on the `main` branch

### v2 — Multi-source, interactive wizard
- Added support for multiple newspapers (ACM, MIT, NYT, BBC)
- Created `setup_wizard.py` — a guided interactive terminal experience
- Created `sources.py` — a registry of available newspaper feeds
- Refactored `scraper.py` and `emailer.py` for multi-source digests
- No manual file editing required

### v3 — Automatic scheduling
- Added `scheduler.py` — installs daily schedules on each OS
  - macOS: LaunchAgent plist in `~/Library/LaunchAgents/`
  - Linux: crontab entry (user-level, no sudo)
  - Windows: Task Scheduler via `schtasks.exe`
- The wizard asks if users want automatic delivery and at what time
- Added `cli.py` — a 9-option interactive menu for managing the installation

### v4 — One-line installers (current)
- Created `install.sh` for macOS/Linux — download, verify, extract, bootstrap
- Created `install.ps1` for Windows PowerShell — same flow, different shell
- Created `build_release.py` — builds distributable zip + checksums
- Created `news-digest` (bash) and `news-digest.ps1` (PowerShell) CLI wrappers
- SHA-256 checksum verification of downloaded packages
- Added `paths.py` — cross-platform Python path helpers
- Added CI via GitHub Actions — tests on macOS, Linux, and Windows

## Design philosophy

Five principles guide every decision in this codebase:

### 1. Fail fast, fail loud
If something goes wrong, the code tells you immediately with a clear error message. No silent failures, no swallowed exceptions, no "it worked" when it didn't.

**Example:** In `main.py`, if `SELECTED_SOURCES` is empty, the program prints a helpful message and exits immediately rather than trying to send an empty email.

### 2. Single Responsibility
Each module has one reason to change. The scraper only knows about RSS parsing. The emailer only knows about formatting and sending. The scheduler only knows about OS-level scheduling.

### 3. Dataclasses over dicts
Structured data uses Python dataclasses instead of plain dictionaries. A `NewsSource` dataclass gives you named fields (`source.name`), IDE autocompletion, typo protection, and a single place to see what a "source" is.

### 4. Heavily commented code
Every function and every significant block of code has a comment explaining *what* it does and *why*. The code is meant to be readable by people learning to program.

### 5. Cross-platform by default
Every feature works on macOS, Linux, and Windows. When platform-specific code is necessary (like scheduling), each platform gets its own implementation behind a unified API.

## Technology stack

| Component | Technology | Why |
|-----------|-----------|-----|
| Language | Python 3.10+ | Readable, beginner-friendly, cross-platform, rich stdlib |
| HTTP client | `requests` | De facto standard, handles timeouts/retries gracefully |
| Config | `python-dotenv` | Loads `.env` files without polluting global environment |
| XML parsing | `xml.etree.ElementTree` | Built into Python, no extra install needed |
| Email | `smtplib` + `email.mime` | Built into Python, direct SMTP control |
| Scheduling (macOS) | LaunchAgent plist | Native macOS mechanism, user-level, no sudo |
| Scheduling (Linux) | crontab | Universal Linux scheduling, user-level |
| Scheduling (Windows) | schtasks.exe | Built into all modern Windows |
| Testing | pytest | Most popular Python test framework, clear output |
| CI | GitHub Actions | Free for public repos, matrix strategy for cross-platform |
| Release | Custom `build_release.py` | Full control over what goes into the package |

## Key constraints

- **Gmail SMTP only** — uses App Passwords with 2-Factor Authentication. No other email providers are supported, because Gmail is what the target audience already uses.
- **Free RSS feeds only** — we can only scrape newspapers that provide public RSS/XML feeds. No paywalled content, no API keys, no scraping rendered HTML.
- **No external services** — everything runs locally on the user's computer. No server, no database, no cloud account needed.
- **Minimal dependencies** — only two pip packages (`requests` and `python-dotenv`). Everything else is Python's standard library.
