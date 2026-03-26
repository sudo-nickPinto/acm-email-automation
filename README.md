# News Digest — Your Personal Newspaper Email

> Pick your newspapers. Get a daily digest. All from your terminal.

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform: macOS | Linux | Windows](https://img.shields.io/badge/platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey.svg)]()

## What is this?

A terminal tool that sends you a daily email digest of news articles from newspapers you choose. You pick your sources, enter your Gmail, and you're done — your news shows up in your inbox, automatically.

**Available sources:**
- ACM TechNews — curated computing & tech articles (Mon/Wed/Fri)
- MIT Technology Review — emerging technology analysis
- The New York Times — Technology section
- BBC News — Technology section

**No coding knowledge required.** The setup wizard walks you through everything.

## Install

Open your terminal and paste the command for your OS.

Recommended path: download the installer first, then run it locally.

### macOS / Linux

```bash
curl -fsSLO https://github.com/sudo-nickPinto/acm-email-automation/releases/latest/download/install.sh
bash install.sh
```

### Windows (PowerShell)

```powershell
iwr https://github.com/sudo-nickPinto/acm-email-automation/releases/latest/download/install.ps1 -OutFile install.ps1
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

Fast-path alternative: if you accept the risk of executing the installer directly from the network stream, the release still supports `curl ... | bash` and `irm ... | iex`.

That's it. The installer downloads a packaged release, verifies it with `SHA256SUMS.txt`, extracts it, and launches the bootstrap flow. The bootstrap then checks for Python, creates a virtual environment, installs the pinned runtime packages from `requirements.lock`, and launches the setup wizard.

> **Already have git?** You can also clone directly:
> ```bash
> git clone https://github.com/sudo-nickPinto/acm-email-automation.git
> cd acm-email-automation && chmod +x start.sh && ./start.sh
> ```

## How It Works

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌────────┐
│  RSS Feeds   │────►│  scraper.py  │────►│  emailer.py  │────►│  Gmail │
│  (4 sources) │     │  Parse XML   │     │  Format HTML │     │  SMTP  │
└──────────────┘     │  → Articles  │     │  + Send      │     └────────┘
                     └──────────────┘     └──────────────┘
```

The setup wizard:
1. Asks which newspapers you want
2. Walks you through Gmail App Password setup
3. Optionally sets up **automatic daily delivery** (LaunchAgent on macOS, cron on Linux, Task Scheduler on Windows)
4. Offers to send a test email

After setup, your digest arrives automatically — or manage everything through the interactive menu:

```bash
news-digest                         # Launch interactive menu
```

The menu lets you:
- Send your digest now, preview it, or force-resend
- Change your newspaper sources, email, or app password
- Adjust or disable automatic scheduling
- View current status
- Uninstall everything

You can also run commands directly:

```bash
news-digest run                     # Send the digest
news-digest run --dry-run            # Preview without sending
news-digest run --force              # Resend even if already sent today
news-digest status                   # Show current configuration
news-digest setup                    # Re-run the setup wizard
news-digest uninstall                # Remove everything
```

## Publish For Friends

Build the release assets with:

```bash
python3 scripts/build_release.py
```

Run that from a clean, committed worktree. For an intentional local smoke build from uncommitted changes, use:

```bash
NEWSDIGEST_ALLOW_DIRTY=1 python3 scripts/build_release.py
```

That creates:
- `dist/news-digest.zip`
- `dist/SHA256SUMS.txt`
- `dist/install.sh`
- `dist/install.ps1`
- `dist/SHARE_THIS.txt`

Upload the first four files to a GitHub Release. `SHARE_THIS.txt` is a maintainer note you can keep locally.

Security note: `SHA256SUMS.txt` helps detect corruption or mismatched artifacts, but it does not independently authenticate the release origin because the installer, ZIP, and checksum all come from the same GitHub release channel. The download URL itself is still a trust boundary today. Signed releases are the next stronger step.

## Project Structure

```
acm_email_automation/
├── install.sh               # One-line installer (macOS / Linux)
├── install.ps1              # One-line installer (Windows)
├── scripts/
│   └── build_release.py     # Builds the release assets for sharing
├── start.sh                 # Bootstrap + setup wizard launcher
├── setup_wizard.py          # Interactive terminal setup
├── main.py                  # Entry point / orchestrator
├── news-digest              # Shell wrapper CLI (installed into a writable PATH dir)
├── newsdigest/              # Core Python package
│   ├── __init__.py
│   ├── config.py            # Loads settings from .env
│   ├── sources.py           # Registry of newspaper RSS feeds
│   ├── scraper.py           # Fetches + parses RSS feeds
│   ├── emailer.py           # Formats + sends the email
│   ├── scheduler.py         # Installs daily schedule per OS
│   └── cli.py               # Interactive menu system
├── requirements.txt         # Human-edited direct dependency list
├── requirements.lock        # Pinned runtime dependency versions used by installers
├── tests/                   # Test suite (pytest)
│   ├── conftest.py          # Shared fixtures
│   ├── test_sources.py      # Source registry tests
│   ├── test_scraper.py      # RSS scraper tests
│   ├── test_emailer.py      # Email formatter tests
│   ├── test_scheduler.py    # Scheduler tests
│   ├── test_config.py       # Config loading tests
│   ├── test_main.py         # Orchestrator tests
│   └── test_cli.py          # Interactive menu tests
├── .env.example             # Template for configuration
├── docs/                    # Full documentation
└── .gitignore
```

## Changing Your Settings

Use the interactive menu:

```bash
news-digest
```

Or re-run the full setup wizard:

```bash
./start.sh
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `SMTPAuthenticationError` | Regenerate your Gmail App Password and re-run `./start.sh` |
| "No news sources configured" | Run `./start.sh` to select your sources |
| "No articles found" | RSS feeds may be temporarily unavailable |
| "Already sent this digest" | Use `--force` to resend, or wait for new articles |
| Python not found after install | Close and reopen your terminal, then run `./start.sh` again |

## Testing

Run the test suite (131 tests, all offline — no network or email required):

```bash
venv/bin/python3 -m pytest tests/ -v
```

## Documentation

Full documentation lives in [`docs/`](docs/). Start with the [docs README](docs/README.md) for a reading guide.

## License

MIT
