# 01 — Project Overview

## What Is This Project?

This is a terminal tool that sends you a daily email digest of news articles from newspapers you choose. You select your sources, enter your Gmail, and the tool delivers the articles straight to your inbox.

**v3** (this version) supports multiple newspaper sources, automatic daily scheduling, and one-command installation. You pick which newspapers you want during an interactive setup wizard — no configuration files to edit, no code to touch.

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
1. Run the release installer (or `./start.sh` if you cloned the repo) — the bootstrap flow handles everything
2. Your digest arrives automatically every day at the time you chose
3. Or run `venv/bin/python3 main.py` whenever you want it on-demand
4. One email, all your sources, neatly organized by newspaper

That's it.

## Who Is This For?

This was built to share with friends — people who don't code. They paste one or two commands into their terminal and the installer handles the rest: downloading the project, verifying the packaged release, checking whether Python is installed, walking through Gmail setup, and setting up automatic daily delivery. No git, no GitHub account, no coding knowledge required.

For maintainers, the release flow is separate: build a packaged ZIP, publish `SHA256SUMS.txt`, and upload the installer assets to a GitHub Release. The friend-facing install command points at `releases/latest/download`, so users never need to clone the repo.

## Project File Map

Here's every file and what it does:

| File | Role | Analogy |
|------|------|---------|
| `install.sh` | One-line installer (macOS/Linux) | The front door |
| `install.ps1` | One-line installer (Windows) | The front door (Windows) |
| `start.sh` | Bootstrap + setup wizard launcher | The installer |
| `setup_wizard.py` | Interactive source/email/schedule config | The setup assistant |
| `main.py` | Entry point / orchestrator | The conductor |
| `newsdigest/sources.py` | Registry of available newspapers | The newspaper stand |
| `newsdigest/scraper.py` | Fetches and parses RSS feeds | The delivery person |
| `newsdigest/emailer.py` | Formats and sends the digest email | The layout editor + postal service |
| `newsdigest/scheduler.py` | Installs daily schedule per OS | The alarm clock |
| `newsdigest/config.py` | Loads settings from `.env` | The settings panel |
| `requirements.txt` | Human-edited direct dependencies | The shopping list |
| `requirements.lock` | Pinned runtime dependency versions | The exact order |
| `.env` | User's config (git-ignored) | The locked filing cabinet |
| `.env.example` | Template for `.env` | The blank form |
| `.last_sent` | Hash of the last-sent edition | The "already read" bookmark |

## How the Pieces Fit Together

```
┌──────────────────────────────────────────────────────────────────────┐
│  install.sh / install.ps1                                                │
│  1. Downloads the packaged release from GitHub (no git needed)           │
│  2. Verifies the package checksum                                        │
│  3. Extracts to ~/news-digest                                            │
│  4. Launches start.sh                                                    │
└────────────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌────────────────────────────────────────────────────────────────────┐
│  start.sh                                                                │
│  1. Checks for Python and shows install guidance if missing              │
│  2. Creates virtual environment                                          │
│  3. Installs pinned runtime packages                                     │
│  4. Launches setup_wizard.py                                             │
└──────────────────────────┤─────────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────────────────┐
│  setup_wizard.py                                                     │
│  1. Pick your newspapers (numbered list)                             │
│  2. Enter Gmail address                                              │
│  3. Create Gmail App Password (guided instructions)                  │
│  4. Set up automatic daily delivery (optional)                       │
│  5. Writes .env automatically                                        │
│  6. Offers to send a test email                                      │
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
# Recommended install (no git required)
curl -fsSLO https://github.com/sudo-nickPinto/acm-email-automation/releases/latest/download/install.sh
bash install.sh

# Or if you cloned the repo:
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

Security note: the checksum helps verify the downloaded package, but the release source itself is still a trust boundary. If the GitHub release or account were compromised, users could still be served a bad installer. Signed releases are the next step up in assurance.

---

**Next:** [02 — System Design](02-system-design.md)
