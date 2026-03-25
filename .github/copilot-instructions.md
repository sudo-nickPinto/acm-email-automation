# Project: News Digest Email Automation (v2)

## What this project is
A terminal-first tool that sends users a daily email digest of news articles from newspapers they choose. Users clone the repo, run `./start.sh`, and a guided terminal wizard handles everything — Python installation, newspaper selection, email configuration.

## Current state
- **Branch:** `public_attempt` (all v2 work happens here; `main` stays as v1)
- **v1 (main branch):** ACM TechNews only, single RSS source, manual `.env` setup
- **v2 (this branch):** Multi-source newspaper digest, interactive terminal setup, no manual file editing

## Architecture
```
start.sh              → Bootstrap: installs Python, creates venv, hands off to Python wizard
setup_wizard.py       → Interactive CLI: newspaper selection, email config, writes .env
newsdigest/           → Core package (renamed from acm_technews/)
  config.py           → Loads .env, exposes constants
  sources.py          → Registry of newspaper RSS feeds with metadata
  scraper.py          → Fetches/parses RSS feeds (multi-source)
  emailer.py          → Formats and sends multi-source digest email
main.py               → Orchestrator: fetch → deduplicate → send
```

## Key constraints
- **Target audience:** Non-technical users (friends). Zero coding knowledge assumed.
- **Minimal prerequisites:** Only a terminal and a Gmail account. Python install is guided.
- **Terminal-first:** All setup happens interactively in the terminal. No manual file editing.
- **macOS + Linux:** Must work on both. `start.sh` detects OS and adjusts.
- **Gmail SMTP only:** Uses App Passwords with 2FA. The wizard explains how to get one.
- **Free RSS feeds only:** We can only scrape newspapers that provide public RSS feeds.

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
- `./start.sh` — Full bootstrap + setup wizard
- `venv/bin/python3 main.py --dry-run` — Preview without sending
- `venv/bin/python3 main.py` — Send the digest
- `venv/bin/python3 main.py --force` — Bypass duplicate detection
