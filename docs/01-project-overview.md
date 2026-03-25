# 01 — Project Overview

## What Is This Project?

This is a terminal tool that sends you a daily email digest of news articles from newspapers you choose. You select your sources, enter your Gmail, and the tool delivers the articles straight to your inbox.

**v2** (this version) supports multiple newspaper sources. You pick which ones you want during an interactive setup wizard — no configuration files to edit, no code to touch.

**Available sources:**

| Source | Description |
|--------|-------------|
| ACM TechNews | Curated computing & technology articles (Mon/Wed/Fri) |
| MIT Technology Review | Emerging technology analysis |
| The New York Times — Technology | NYT's tech section |
| BBC News — Technology | BBC's tech coverage |

## What Problem Does It Solve?

Without this tool:
1. You visit multiple news sites every day
2. You bookmark, forget, or bounce between tabs
3. You miss articles because you skip a day

With this tool:
1. Run `./start.sh` once — the wizard handles everything
2. Run `venv/bin/python3 main.py` when you want your digest
3. One email, all your sources, neatly organized by newspaper

That's it.

## Who Is This For?

This was built to share with friends — people who don't code. The setup wizard explains every step in plain language, installs Python if it's missing, and walks you through Gmail configuration. The only prerequisite is a terminal and a Gmail account.

## Project File Map

Here's every file and what it does:

| File | Role | Analogy |
|------|------|---------|
| `start.sh` | Bootstrap + setup wizard launcher | The installer |
| `setup_wizard.py` | Interactive source/email config | The setup assistant |
| `main.py` | Entry point / orchestrator | The conductor |
| `newsdigest/sources.py` | Registry of available newspapers | The newspaper stand |
| `newsdigest/scraper.py` | Fetches and parses RSS feeds | The delivery person |
| `newsdigest/emailer.py` | Formats and sends the digest email | The layout editor + postal service |
| `newsdigest/config.py` | Loads settings from `.env` | The settings panel |
| `requirements.txt` | Python dependencies | The shopping list |
| `.env` | User's config (git-ignored) | The locked filing cabinet |
| `.env.example` | Template for `.env` | The blank form |
| `.last_sent` | Hash of the last-sent edition | The "already read" bookmark |

## How the Pieces Fit Together

```
┌──────────────────────────────────────────────────────────────────────┐
│  start.sh                                                            │
│  1. Installs Python (if needed)                                      │
│  2. Creates virtual environment                                      │
│  3. Launches setup_wizard.py                                         │
└───────────────────────┬──────────────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────────────────┐
│  setup_wizard.py                                                     │
│  1. Pick your newspapers (numbered list)                             │
│  2. Enter Gmail address                                              │
│  3. Create Gmail App Password (guided instructions)                  │
│  4. Writes .env automatically                                        │
│  5. Offers to send a test email                                      │
└──────────────────────────────────────────────────────────────────────┘


┌──────────────────────────────────────────────────────────────────────┐
│  main.py                                                             │
│  1. Calls scraper.fetch_all_sources()                                │
│  2. Hashes article titles → compares with .last_sent                 │
│  3. If new articles → calls emailer.send_email()                     │
│  4. Saves hash to .last_sent                                         │
└──────┬────────────────────────────────┬──────────────────────────────┘
       │                                │
       ▼                                ▼
┌──────────────────┐          ┌───────────────────────┐
│  scraper.py      │          │  emailer.py           │
│  HTTP GET → XML  │          │  Articles → HTML/text │
│  parse → list of │          │  → Gmail SMTP → inbox │
│  Article objects  │          │                       │
│  (multi-source)  │          │  (multi-section)      │
└──────────────────┘          └───────────────────────┘
       │                                │
       ▼                                ▼
┌──────────────────┐          ┌───────────────────────┐
│  sources.py      │          │  config.py            │
│  (RSS feed URLs) │          │  (SMTP credentials +  │
│                  │          │   selected sources)   │
└──────────────────┘          └───────────────────────┘
```

## Running It

```bash
# First time — installs everything and launches setup wizard
chmod +x start.sh
./start.sh

# Preview the email without sending
venv/bin/python3 main.py --dry-run

# Send the digest
venv/bin/python3 main.py

# Force re-send even if articles haven't changed
venv/bin/python3 main.py --force

# Change your sources or email settings
./start.sh
```

---

**Next:** [02 — System Design](02-system-design.md)
