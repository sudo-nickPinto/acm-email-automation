# ACM TechNews Email Automation

> Automatically fetches the latest [ACM TechNews](https://technews.acm.org/) digest and delivers a formatted summary to your inbox.

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform: macOS](https://img.shields.io/badge/platform-macOS-lightgrey.svg)]()

## Overview

ACM TechNews publishes curated computing and technology articles three times per week (Monday, Wednesday, Friday). This tool parses the RSS feed, formats the articles into a clean email digest, and sends it via Gmail SMTP — all on autopilot.

**Features:**
- Parses the ACM TechNews RSS/XML feed into structured data
- Sends a multipart email (HTML + plain text) via Gmail SMTP
- Schedules automatically on macOS using `launchd` (Mon/Wed/Fri at 8 AM)
- Detects duplicate editions via SHA-256 hashing to avoid repeat emails
- Supports `--dry-run` to preview and `--force` to resend

## Project Structure

```
acm_email_automation/
├── acm_technews/            # Core Python package
│   ├── __init__.py
│   ├── config.py            # Loads settings from .env
│   ├── scraper.py           # Fetches + parses the RSS feed
│   └── emailer.py           # Formats + sends the email
├── main.py                  # Entry point / orchestrator
├── setup.sh                 # One-command install + scheduling
├── requirements.txt         # Python dependencies
├── .env.example             # Template for environment variables
└── .gitignore
```

## Quick Start

### Prerequisites

- **macOS** (for `launchd` scheduling; the Python code is cross-platform)
- **Python 3.10+**
- **Gmail account** with [2-Step Verification](https://myaccount.google.com/security) enabled

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/acm_email_automation.git
cd acm_email_automation
```

### 2. Create a Gmail App Password

Gmail requires an App Password when 2FA is enabled:

1. Go to [Google Account → App Passwords](https://myaccount.google.com/apppasswords)
2. Select **Mail** and generate a password
3. Copy the 16-character code

### 3. Configure environment

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
SMTP_EMAIL=your_email@gmail.com
SMTP_APP_PASSWORD=abcd efgh ijkl mnop
RECIPIENT_EMAIL=recipient@gmail.com
```

### 4. Run setup

```bash
chmod +x setup.sh
./setup.sh
```

This creates a virtual environment, installs dependencies, and registers a macOS Launch Agent on the Mon/Wed/Fri schedule.

## Usage

```bash
# Preview the email in the terminal (no email sent)
venv/bin/python3 main.py --dry-run

# Send the email
venv/bin/python3 main.py

# Force resend even if this edition was already sent
venv/bin/python3 main.py --force
```

## How It Works

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌────────┐
│  ACM RSS     │────►│  scraper.py  │────►│  emailer.py  │────►│  Gmail │
│  Feed (XML)  │     │  Parse XML   │     │  Format HTML │     │  SMTP  │
└──────────────┘     │  → Articles  │     │  + Send      │     └────────┘
                     └──────────────┘     └──────────────┘
                              ▲                    ▲
                              │                    │
                         config.py            config.py
                        (RSS URL)          (SMTP creds)
```

1. **`main.py`** orchestrates the pipeline: fetch → deduplicate → send
2. **`scraper.py`** makes an HTTP GET to the RSS feed, parses the XML, and returns a list of `Article` dataclass objects
3. **`emailer.py`** builds both HTML and plain-text email bodies, then sends via SMTP with TLS
4. **Duplicate detection** hashes article titles with SHA-256 and stores the hash in `.last_sent`; skips sending if the hash matches the previous run

## Scheduling

The setup script installs a macOS `launchd` agent that runs automatically.

```bash
# Check job status
launchctl list | grep acm

# Manually trigger
launchctl start com.acm.technews.email

# View logs
cat logs/stdout.log
cat logs/stderr.log

# Uninstall
launchctl unload ~/Library/LaunchAgents/com.acm.technews.email.plist
rm ~/Library/LaunchAgents/com.acm.technews.email.plist
```

## Configuration

All settings are loaded from a `.env` file via [python-dotenv](https://pypi.org/project/python-dotenv/). See [`.env.example`](.env.example) for the required variables.

| Variable | Required | Description |
|----------|----------|-------------|
| `SMTP_EMAIL` | Yes | Gmail address used to send the email |
| `SMTP_APP_PASSWORD` | Yes | Gmail App Password (not your regular password) |
| `RECIPIENT_EMAIL` | Yes | Email address that receives the digest |

## Dependencies

| Package | Purpose |
|---------|---------|
| [requests](https://docs.python-requests.org/) | HTTP client for fetching the RSS feed |
| [python-dotenv](https://pypi.org/project/python-dotenv/) | Loads `.env` file into environment variables |
| [beautifulsoup4](https://www.crummy.com/software/BeautifulSoup/) | HTML parsing (reserved for future use) |

All other functionality uses Python's standard library (`smtplib`, `xml.etree`, `hashlib`, `email.mime`, `pathlib`).

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `SMTPAuthenticationError` | Regenerate your Gmail App Password and update `.env` |
| "Already sent email for this edition" | Expected — use `--force` to resend, or wait for the next edition |
| "No articles found" | The RSS feed may be temporarily unavailable |
| `ModuleNotFoundError` | Run `venv/bin/pip install -r requirements.txt` |
| Job not running on schedule | Verify with `launchctl list \| grep acm`; re-run `./setup.sh` |

## License

MIT
