# News Digest — Your Personal Newspaper Email

> Pick your newspapers. Get a daily digest. All from your terminal.

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform: macOS | Linux](https://img.shields.io/badge/platform-macOS%20%7C%20Linux-lightgrey.svg)]()

## What is this?

A terminal tool that sends you a daily email digest of news articles from newspapers you choose. You pick your sources, enter your Gmail, and you're done — your news shows up in your inbox.

**Available sources:**
- ACM TechNews — curated computing & tech articles (Mon/Wed/Fri)
- MIT Technology Review — emerging technology analysis
- The New York Times — Technology section
- BBC News — Technology section

**No coding knowledge required.** The setup wizard walks you through everything.

## Quick Start

### Prerequisites
- A computer with a terminal (macOS or Linux)
- A Gmail account

That's it. The setup wizard handles Python installation if needed.

### 1. Clone the repository

```bash
git clone https://github.com/sudo-nickPinto/acm-email-automation.git
cd acm-email-automation
```

### 2. Run the setup wizard

```bash
chmod +x start.sh
./start.sh
```

The wizard will:
1. Install Python if you don't have it
2. Ask which newspapers you want
3. Walk you through Gmail App Password setup (with step-by-step instructions)
4. Offer to send a test email

### 3. Send your digest anytime

```bash
venv/bin/python3 main.py          # Send the digest
venv/bin/python3 main.py --dry-run  # Preview without sending
venv/bin/python3 main.py --force    # Resend even if already sent today
```

## How It Works

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌────────┐
│  RSS Feeds   │────►│  scraper.py  │────►│  emailer.py  │────►│  Gmail │
│  (4 sources) │     │  Parse XML   │     │  Format HTML │     │  SMTP  │
└──────────────┘     │  → Articles  │     │  + Send      │     └────────┘
                     └──────────────┘     └──────────────┘
```

1. **`start.sh`** bootstraps Python, creates the virtual environment, and launches the setup wizard
2. **`setup_wizard.py`** walks you through newspaper selection and email config
3. **`main.py`** orchestrates: fetch → deduplicate → send
4. **`newsdigest/scraper.py`** fetches RSS feeds and parses articles
5. **`newsdigest/emailer.py`** formats a multi-section HTML + plain-text email and sends via Gmail SMTP

## Project Structure

```
acm_email_automation/
├── start.sh                 # Run this — bootstraps everything
├── setup_wizard.py          # Interactive terminal setup
├── main.py                  # Entry point / orchestrator
├── newsdigest/              # Core Python package
│   ├── __init__.py
│   ├── config.py            # Loads settings from .env
│   ├── sources.py           # Registry of newspaper RSS feeds
│   ├── scraper.py           # Fetches + parses RSS feeds
│   └── emailer.py           # Formats + sends the email
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
