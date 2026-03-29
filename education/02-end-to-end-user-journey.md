# Lesson 02 — End-to-End User Journey

This lesson walks through the complete experience of a user — from the moment they decide to install News Digest to the moment they receive their first email digest. Understanding this journey helps you see why every component exists and how they connect.

## The journey in six acts

### Act 1: The friend receives a message

A friend sends them a message:

> "Hey, I built a tool that sends you a daily email with tech news. Paste this into your terminal:"
>
> ```
> curl -fsSLO https://github.com/.../install.sh && bash install.sh
> ```

Or, for Windows PowerShell:

> ```
> iwr https://github.com/.../install.ps1 -OutFile install.ps1; powershell -ExecutionPolicy Bypass -File .\install.ps1
> ```

**Files involved:** `install.sh`, `install.ps1`

### Act 2: The installer runs

When the user pastes that command:

1. **Download** — The installer downloads `news-digest.zip` from the latest GitHub Release
2. **Verify** — It downloads `SHA256SUMS.txt` and computes the SHA-256 hash of the zip file, comparing the two. If they do not match, the installer refuses to continue (protects against corrupted or tampered downloads)
3. **Extract** — The zip is extracted to `~/news-digest`
4. **Validate** — The installer checks that the extracted folder contains the expected files (`start.sh`, `setup_wizard.py`, etc.)
5. **Install CLI command** — A symlink (macOS/Linux) or `.cmd` wrapper (Windows) is placed on the user's PATH so they can type `news-digest` from anywhere
6. **Launch bootstrap** — The installer launches `start.sh` (macOS/Linux) or runs the Python setup directly (Windows)

**Files involved:** `install.sh`, `install.ps1`, `scripts/build_release.py` (created the zip)

### Act 3: The bootstrap runs

`start.sh` is the bootstrap script that gets the Python environment ready:

1. **Check for Python** — Tries `python3`, `python`, `python3.13`, `python3.12`, etc. looking for Python 3.10+
2. **Guide Python install** — If Python is not found, it prints step-by-step instructions specific to the user's OS (Homebrew for macOS, apt/dnf for Linux, python.org for Windows)
3. **Create virtual environment** — Runs `python3 -m venv venv` to create an isolated Python environment in the project folder
4. **Install dependencies** — Runs `pip install -r requirements.lock` (or `requirements.txt`) inside the venv
5. **Launch the wizard** — Runs `venv/bin/python3 setup_wizard.py`

**Why a virtual environment?** A venv is a self-contained Python installation inside the project folder. It means the project's dependencies (like `requests`) do not conflict with anything else on the user's computer, and uninstalling is as simple as deleting the folder.

**Files involved:** `start.sh`, `requirements.txt`, `requirements.lock`

### Act 4: The setup wizard runs

`setup_wizard.py` is a 5-step interactive questionnaire:

**Step 1 — Choose sources:** The wizard displays a numbered list of available newspapers:
```
  [1] ACM TechNews
      Curated computing & technology articles from ACM (Mon/Wed/Fri)

  [2] MIT Technology Review
      Emerging technology analysis from MIT

  [3] The New York Times — Technology
      ...

  [4] BBC News — Technology
      ...

  Enter the numbers of the sources you want: 1 3 4
```

**Step 2 — Email address:** Asks for the user's Gmail address (validates that it ends with `@gmail.com`).

**Step 3 — App Password:** This is the trickiest part. Gmail does not allow apps to use your regular password. Instead, users need a 16-character "App Password" from Google. The wizard provides detailed step-by-step instructions, including the exact URL to visit and what buttons to click.

**Step 4 — Schedule:** Asks if the user wants automatic daily delivery and at what time (e.g., `08:00`). If they say yes, the wizard calls `scheduler.py` to install a LaunchAgent (macOS), cron job (Linux), or Scheduled Task (Windows).

**Step 5 — Test email:** Offers to send a test email immediately to verify everything works.

The wizard writes all answers to a `.env` file (a simple `KEY=value` text file) and restricts its permissions to owner-only (`chmod 600`) so other users on the same computer cannot read the password.

**Files involved:** `setup_wizard.py`, `newsdigest/sources.py`, `newsdigest/scheduler.py`, `.env` (created)

### Act 5: The digest runs (manually or automatically)

When the digest runs — either because the schedule triggered it, or the user ran `news-digest run`:

1. **Load config** — `config.py` reads `.env` and exposes the settings as Python constants
2. **Fetch RSS feeds** — `scraper.py` makes HTTP GET requests to each selected newspaper's RSS URL, parses the XML, and extracts articles (title, description, link, publication date)
3. **Filter for freshness** — Only articles published today (in the user's local timezone) are kept
4. **Check for duplicates** — `main.py` computes a SHA-256 hash of all article titles + today's date and compares it to `.last_sent`. If they match, the digest was already sent and it exits
5. **Format the email** — `emailer.py` builds both a plain-text version and an HTML version with styled sections per newspaper, colored headers, and "Read full article" links
6. **Send via SMTP** — Connects to `smtp.gmail.com:587`, starts TLS encryption, authenticates with the App Password, and sends the email
7. **Save state** — Writes the hash to `.last_sent` so we know this edition was sent

**Files involved:** `main.py`, `newsdigest/config.py`, `newsdigest/scraper.py`, `newsdigest/emailer.py`

### Act 6: The email arrives

The user opens their Gmail inbox and sees an email with:
- Subject: "Your News Digest — March 25, 2025"
- Time-appropriate greeting ("Good morning", "Good afternoon", or "Good evening")
- Sections per newspaper with colored headers
- Each article showing: title, description blurb, and a "Read full article" link
- A footer explaining how to manage settings

## What the user can do after setup

Once installed, the user has several options:

| Command | What it does |
|---------|-------------|
| `news-digest` | Opens the interactive 9-option menu |
| `news-digest run` | Sends the digest right now |
| `news-digest run --dry-run` | Previews the digest without sending |
| `news-digest run --force` | Re-sends even if already sent today |
| `news-digest setup` | Re-runs the setup wizard |
| `news-digest status` | Shows current config and schedule info |
| `news-digest uninstall` | Removes schedule, files, and CLI command |

## Data flow summary

```
RSS Feeds (HTTP)
    |
    v
scraper.py --- parses XML ---> list[SourceResult]
                                    |
                                    v
main.py --- filters today's --- deduplicates ---> emailer.py
                                                      |
                                                      v
                                              Gmail SMTP (TLS)
                                                      |
                                                      v
                                                User's Inbox
```

This pipeline is the core of the project. In the upcoming lessons, we will look at each stage in detail.
