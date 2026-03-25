# 08 — Bootstrap, Setup, and Scheduling

## The Full Bootstrap Chain

Getting from "my friend opened a terminal" to "they're receiving daily news digests" requires a chain of scripts:

1. **`install.sh`** / **`install.ps1`** — one-line installers that download the project (no git required)
2. **`start.sh`** — a bash script that gets Python installed, creates a virtual environment, installs dependencies, and launches the wizard
3. **`setup_wizard.py`** — a Python script that handles newspaper selection, Gmail setup, scheduling, and writes the `.env` file
4. **`newsdigest/scheduler.py`** — installs a daily schedule using OS-native tools

## `install.sh` / `install.ps1` — The One-Line Installers

These scripts exist so friends don't need git or a GitHub account. They paste one command into their terminal:

**macOS / Linux:**
```bash
curl -fsSL https://raw.githubusercontent.com/sudo-nickPinto/acm-email-automation/public_attempt/install.sh | bash
```

**Windows (PowerShell):**
```powershell
irm https://raw.githubusercontent.com/sudo-nickPinto/acm-email-automation/public_attempt/install.ps1 | iex
```

### What they do

1. Download the project as a `.zip` from GitHub's archive URL (no git clone)
2. Extract to `~/news-digest` (or `$HOME\news-digest` on Windows)
3. If an existing installation is found, offer to reinstall
4. Launch `start.sh` (or run the equivalent bootstrap steps directly on Windows)

`install.sh` uses `curl` + `unzip` with a Python `zipfile` fallback if `unzip` isn't available.
`install.ps1` uses `Invoke-WebRequest` + `Expand-Archive` (built into PowerShell 5+).

## `start.sh` — The Bootstrap Script

This is the only file the user runs directly. It handles the chicken-and-egg problem: you need Python to run Python code, so you need a shell script to check for (and install) Python first.

### Key Concepts

**The shebang:**
```bash
#!/bin/bash
```
Tells the OS to run this file with bash. Without it, the OS doesn't know which interpreter to use.

**Strict mode:**
```bash
set -e
```
Exit immediately if any command fails. Without this, a failed command would be silently ignored and the script would continue in a broken state.

**Locating the project:**
```bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
```
Finds the directory containing the script, regardless of where it's called from. This means `cd ~/Downloads && /path/to/start.sh` still works.

### Step 1: Python Detection

```bash
find_python() {
    for cmd in python3 python python3.13 python3.12 python3.11 python3.10; do
        if check_python "$cmd"; then
            echo "$cmd"
            return 0
        fi
    done
    return 1
}
```

The script tries several common Python command names. `check_python` verifies both that the command exists and that the version is ≥ 3.10.

If no Python is found, the script detects the OS and provides installation instructions:

- **macOS:** Offers two paths — download from python.org (recommended for beginners), or install via Homebrew (`brew install python3`) if Homebrew is already present
- **Linux:** Detects the package manager (apt, dnf, or pacman) and shows the correct install command
- **Windows (Git Bash / MSYS2 / Cygwin):** Directs users to python.org or `winget install Python.Python.3.12`, emphasizing "Add Python to PATH" during install
- **Unknown OS:** Falls back to a link to python.org

After showing instructions, the script pauses and waits for the user to confirm they've installed Python, then re-checks.

### OS Detection

```bash
detect_os() {
    case "$(uname -s)" in
        Darwin*)  echo "macos" ;;
        Linux*)   echo "linux" ;;
        MINGW*|MSYS*|CYGWIN*) echo "windows" ;;
        *)        echo "unknown" ;;
    esac
}
```

On Windows, `start.sh` adjusts venv paths (`Scripts/` instead of `bin/`) and pip commands accordingly.

### Step 2: Virtual Environment + Dependencies

```bash
"$PYTHON_CMD" -m venv "$SCRIPT_DIR/venv"
"$SCRIPT_DIR/venv/bin/pip" install -q -r "$SCRIPT_DIR/requirements.txt"
```

Creates an isolated Python environment with its own packages. This prevents conflicts with system-wide Python packages.

### Step 3: Launch the Setup Wizard

```bash
"$SCRIPT_DIR/venv/bin/python3" "$SCRIPT_DIR/setup_wizard.py"
```

Hands off to the Python-based wizard for interactive configuration. The script's job is done — everything from here runs in Python.

## `setup_wizard.py` — The Interactive Setup

### Design Philosophy

This wizard is designed for people who have never opened a terminal before. Every prompt:
- Explains what it's asking and why
- Validates input and gives clear error messages
- Never uses unexplained jargon

### The Flow

```
run_wizard()
  │
  ├── Check for existing .env → offer to keep or reconfigure
  │
  ├── Step 1: _prompt_sources()
  │   └── Show numbered list of newspapers → collect selection
  │
  ├── Step 2: _prompt_email()
  │   └── Ask for Gmail address → validate @gmail.com
  │
  ├── Step 3: _prompt_app_password()
  │   └── Explain App Passwords → show how-to steps → collect password
  │
  ├── Step 4: _prompt_schedule()
  │   └── Ask if user wants daily auto-delivery → pick time → install schedule
  │
  ├── _write_env()
  │   └── Write .env file automatically (including SCHEDULE_TIME)
  │
  ├── Step 5: _offer_test()
  │   └── Offer to send a test email → run main.py as subprocess
  │
  └── Show "Setup Complete" with quick reference commands
```

### Source Selection (`_prompt_sources`)

Displays a numbered list of available newspapers from `newsdigest/sources.py`:

```
  [1] ACM TechNews
      Curated computing & technology articles from ACM (Mon/Wed/Fri)

  [2] MIT Technology Review
      Emerging technology analysis from MIT

  [3] The New York Times — Technology
      Technology coverage from the NYTimes

  [4] BBC News — Technology
      Technology news from the BBC

  Enter the numbers of the sources you want, separated by spaces.
  Example: 1 3 4  (or 'all' for everything)
```

The user types numbers like `1 3 4` or the word `all`. Input is validated — bad numbers, empty input, and non-numeric characters all get helpful error messages.

### Email Validation (`_prompt_email`)

Validates that the input ends with `@gmail.com` (this tool only supports Gmail SMTP).

### App Password Walkthrough (`_prompt_app_password`)

This is the trickiest part for non-technical users. The wizard prints step-by-step instructions:

1. Open `https://myaccount.google.com/apppasswords`
2. Sign in
3. Enable 2-Step Verification if needed (with link)
4. Type "News Digest" as the app name
5. Click Create
6. Copy the 16-character password

Input validation:
- Strips spaces (Google shows passwords as `abcd efgh ijkl mnop`)
- Checks for exactly 16 characters
- Checks for letters only (no numbers or symbols)

### Writing the `.env` File (`_write_env`)

Generates the `.env` file automatically:

```python
env_content = f"""# News Digest Configuration
# Generated by setup wizard — re-run ./start.sh to change
SMTP_EMAIL={email}
SMTP_APP_PASSWORD={app_password}
RECIPIENT_EMAIL={email}
SELECTED_SOURCES={source_keys}
"""
```

The user never needs to touch a configuration file.

### Test Email (`_offer_test`)

Runs `main.py` as a subprocess to send a real digest. If it fails, the wizard shows common fixes (2-Step Verification not enabled, App Password wrong, etc.).

### Existing Configuration

If `.env` already exists, the wizard asks whether to reconfigure or keep the existing setup. This makes re-running `./start.sh` safe — it won't overwrite settings unless the user explicitly wants to change them.

## `newsdigest/scheduler.py` — Automatic Daily Scheduling

The scheduler makes news delivery automatic. Users choose a time during setup, and the digest arrives daily without any manual action.

### OS-Native Approach

Rather than using a Python-based scheduler (which would require a process running 24/7), we use the OS's own scheduling system:

| OS | Mechanism | Location |
|----|-----------|----------|
| **macOS** | LaunchAgent plist | `~/Library/LaunchAgents/com.newsdigest.daily.plist` |
| **Linux** | crontab | User's crontab (tagged with `# com.newsdigest.daily`) |
| **Windows** | Task Scheduler | `schtasks /TN "NewsDigest"` |

### Public API

```python
install_schedule(hour: int, minute: int) -> None  # Install/update daily schedule
uninstall_schedule() -> None                       # Remove the daily schedule
is_schedule_installed() -> bool                    # Check if a schedule exists
```

### How Each Backend Works

**macOS (LaunchAgent):** Writes a plist XML file that tells `launchd` to run `main.py` daily at the specified time. `launchctl load` activates it immediately. The plist points to the venv's Python interpreter so dependencies are always available.

**Linux (cron):** Adds a crontab entry like `30 8 * * * /path/to/venv/bin/python3 /path/to/main.py`. Uses a unique tag comment so the entry can be found and replaced on subsequent runs.

**Windows (Task Scheduler):** Uses `schtasks.exe /Create /SC DAILY /ST 08:30 /TN "NewsDigest"` to create a scheduled task. The task runs even if the user isn't logged in (with `/RL HIGHEST` if available).

### The Wizard Integration

Step 4 of the setup wizard (`_prompt_schedule`) asks:
1. "Would you like automatic daily delivery?" (y/n)
2. If yes: "What time? (24-hour format, e.g. 08:30)"
3. Validation: checks HH:MM format, 0-23 hours, 0-59 minutes
4. Calls `install_schedule(hour, minute)`
5. The chosen time is saved to `.env` as `SCHEDULE_TIME=08:30`

## Adding a New Source

To add a new newspaper:

1. Find its RSS feed URL
2. Add a `NewsSource(...)` entry to `AVAILABLE_SOURCES` in `newsdigest/sources.py`
3. That's it — the wizard, scraper, and emailer all pick it up automatically

No changes needed to `start.sh`, `setup_wizard.py`, `scraper.py`, or `emailer.py`.

---

**Previous:** [07 — Main Orchestrator](07-main-orchestrator.md)
**Next:** [09 — Best Practices](09-best-practices.md)
