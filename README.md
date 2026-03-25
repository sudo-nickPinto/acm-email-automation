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

## Install (One Command)

Open your terminal and paste the command for your OS:

### macOS / Linux

```bash
curl -fsSL https://raw.githubusercontent.com/sudo-nickPinto/acm-email-automation/public_attempt/install.sh | bash
```

### Windows (PowerShell)

```powershell
irm https://raw.githubusercontent.com/sudo-nickPinto/acm-email-automation/public_attempt/install.ps1 | iex
```

That's it. The installer downloads everything, installs Python if needed, and launches the setup wizard.

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

After setup, your digest arrives automatically — or you can send it manually anytime:

```bash
venv/bin/python3 main.py            # Send the digest
venv/bin/python3 main.py --dry-run  # Preview without sending
venv/bin/python3 main.py --force    # Resend even if already sent today
```

## Project Structure

```
acm_email_automation/
├── install.sh               # One-line installer (macOS / Linux)
├── install.ps1              # One-line installer (Windows)
├── start.sh                 # Bootstrap + setup wizard launcher
├── setup_wizard.py          # Interactive terminal setup
├── main.py                  # Entry point / orchestrator
├── newsdigest/              # Core Python package
│   ├── __init__.py
│   ├── config.py            # Loads settings from .env
│   ├── sources.py           # Registry of newspaper RSS feeds
│   ├── scraper.py           # Fetches + parses RSS feeds
│   ├── emailer.py           # Formats + sends the email
│   └── scheduler.py         # Installs daily schedule per OS
├── requirements.txt         # Python dependencies
├── .env.example             # Template for configuration
├── docs/                    # Full documentation
└── .gitignore
```

## Changing Your Settings

Re-run the setup wizard anytime:

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

## Documentation

Full documentation lives in [`docs/`](docs/). Start with the [docs README](docs/README.md) for a reading guide.

## License

MIT
