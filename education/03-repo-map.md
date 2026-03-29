# Lesson 03 — Repo Map

This lesson maps every file and folder in the repository, explaining what each one does and why it exists. Think of this as a tour guide to the codebase — refer back to it whenever you encounter a file you are not sure about.

## Top-level directory

```
acm_email_automation/           <-- project root
|
|-- main.py                     Core pipeline: fetch -> filter -> dedup -> send
|-- setup_wizard.py             Interactive 5-step configuration questionnaire
|-- start.sh                    Bootstrap: checks Python, creates venv, launches wizard
|-- install.sh                  One-line installer for macOS/Linux
|-- install.ps1                 One-line installer for Windows PowerShell
|-- news-digest                 CLI wrapper (bash, symlinked to PATH)
|-- news-digest.ps1             CLI wrapper (PowerShell, wrapped by .cmd file)
|-- requirements.txt            Python package dependencies (requests, python-dotenv, pytest)
|-- requirements.lock           Pinned dependency versions for reproducible installs
|-- README.md                   Public-facing quickstart documentation
|-- .env                        User config (created by wizard, gitignored, chmod 600)
|-- .last_sent                  SHA-256 hash of last sent edition (dedup marker)
|-- .gitignore                  Tells git which files to ignore
|
|-- newsdigest/                 Core Python package
|   |-- __init__.py             Makes this directory a Python package
|   |-- config.py               Loads .env, exposes settings as constants
|   |-- sources.py              Registry of available newspaper RSS feeds
|   |-- scraper.py              Fetches and parses RSS feeds into Article objects
|   |-- emailer.py              Formats digest email (HTML + plain text) and sends via SMTP
|   |-- cli.py                  Interactive 9-option management menu
|   |-- scheduler.py            Installs/removes daily schedule (LaunchAgent, cron, schtasks)
|   |-- paths.py                Cross-platform venv path helpers (is_windows, venv_python_path)
|
|-- scripts/
|   |-- build_release.py        Builds dist/ with zip, checksums, installers
|
|-- tests/                      Full test suite (155 tests, pytest)
|   |-- __init__.py             Makes this directory a Python package
|   |-- conftest.py             Shared pytest fixtures
|   |-- test_main.py            Tests for main.py orchestration logic
|   |-- test_config.py          Tests for config.py loading behavior
|   |-- test_sources.py         Tests for sources.py registry
|   |-- test_scraper.py         Tests for scraper.py parsing and filtering
|   |-- test_emailer.py         Tests for emailer.py formatting and sending
|   |-- test_cli.py             Tests for cli.py menu actions
|   |-- test_scheduler.py       Tests for scheduler.py platform dispatch
|   |-- test_paths.py           Tests for paths.py cross-platform helpers
|   |-- test_install_sh.py      Tests for install.sh bash installer logic
|   |-- test_install_ps1.py     Tests for install.ps1 PowerShell installer logic
|   |-- test_build_release.py   Tests for build_release.py packaging
|
|-- docs/                       Technical documentation (architecture, deep-dives)
|-- education/                  This teaching course (you are here)
|-- logs/                       Output logs from scheduled runs
|-- .github/
|   |-- workflows/
|   |   |-- ci.yml              GitHub Actions CI: cross-platform test matrix
|   |-- copilot-instructions.md Project context for GitHub Copilot
```

## File-by-file details

### main.py (155 lines)
The orchestrator. This is the file that gets run when a user sends their digest. It has four private functions and one `main()` function:

- `_results_hash(results)` — Creates a SHA-256 fingerprint of the current article set
- `_already_sent(hash)` — Checks if `.last_sent` contains this hash
- `_save_state(hash)` — Writes the hash to `.last_sent`
- `main()` — Parses CLI flags, fetches articles, filters to today, deduplicates, sends or previews

### setup_wizard.py (~570 lines)
The guided setup experience. Contains five step functions (`_prompt_sources`, `_prompt_email`, `_prompt_app_password`, `_prompt_schedule`, `_offer_test`) and a `_write_env()` function that creates the `.env` file. Handles stdin/tty reconnection for `curl | bash` invocation.

### start.sh (~200 lines)
The bootstrap script. Detects the OS, finds or helps install Python 3.10+, creates the virtual environment, installs pip packages, and launches `setup_wizard.py`. Uses colorized terminal output with helper functions (`banner`, `info`, `success`, `warn`, `fail`).

### install.sh (~270 lines)
The one-line macOS/Linux installer. Downloads the release zip from GitHub, verifies its SHA-256 checksum (with fallbacks: `shasum`, `sha256sum`, `openssl`), extracts to `~/news-digest`, validates package contents, creates a symlink on PATH, and launches `start.sh`. The entire script is wrapped in a `main()` function so `curl | bash` reads it fully before executing.

### install.ps1 (~320 lines)
The one-line Windows installer. Same logic as `install.sh` but in PowerShell. Uses `Invoke-WebRequest` for downloads, `Get-FileHash` for checksums, `Expand-Archive` for extraction. Creates a `.cmd` wrapper in `AppData/Local/NewsDigest/bin/` and adds it to the user's PATH.

### news-digest (bash, ~115 lines)
The CLI wrapper installed to `/usr/local/bin/` or `~/.local/bin/`. Dispatches subcommands (`run`, `setup`, `status`, `uninstall`, `help`) to the appropriate Python scripts. With no arguments, launches the interactive menu (`cli.py`).

### news-digest.ps1 (PowerShell, ~130 lines)
The Windows CLI wrapper. Same dispatch logic as the bash version, but calls `venv\Scripts\python.exe` and uses PowerShell-native error handling.

### newsdigest/config.py (~75 lines)
Loads `.env` using `python-dotenv` and exposes five constants: `SMTP_EMAIL`, `SMTP_APP_PASSWORD`, `RECIPIENT_EMAIL`, `SELECTED_SOURCES` (parsed list), and `SCHEDULE_TIME`.

### newsdigest/sources.py (~100 lines)
Defines the `NewsSource` dataclass and the `AVAILABLE_SOURCES` list (ACM TechNews, MIT Tech Review, NYT Tech, BBC Tech). Adding a new source is: create a `NewsSource()`, add it to the list, done.

### newsdigest/scraper.py (~250 lines)
Defines `Article` and `SourceResult` dataclasses. Contains `_clean_html()` (strips tags and entities), `_parse_pub_date()` (RFC 822 date parsing with timezone conversion), `_is_published_today()` (freshness check), `_fetch_single_source()` (HTTP GET + XML parse), and `fetch_all_sources()` (iterates selected sources).

### newsdigest/emailer.py (~300 lines)
Defines `build_plain_text()` and `build_html()` (with styled sections, color-cycling headers, article cards) and `send_email()` (SMTP + STARTTLS + login). Contains security helpers `_escape_html_text()` (prevents XSS) and `_safe_href()` (validates URL schemes).

### newsdigest/cli.py (~660 lines)
The interactive management menu with 9 options, each implemented as an `action_*()` function plus a `show_menu()` loop. Handles `.env` reading/writing, config reloading, and subprocess delegation to `main.py`.

### newsdigest/scheduler.py (~400 lines)
Three OS-specific implementations behind a unified API: `install_schedule(hour, minute)`, `uninstall_schedule()`, `is_schedule_installed()`. Each OS has install/uninstall/is_installed triplet functions.

### newsdigest/paths.py (~30 lines)
Three helper functions: `is_windows()`, `venv_python_path(project_root)` (returns the OS-appropriate path to the venv Python binary), `venv_python_command(project_root, target)` (returns a user-facing command string).

### scripts/build_release.py (~180 lines)
Builds `dist/` containing: `news-digest.zip` (the distributable package), `SHA256SUMS.txt` (checksums), copies of the installers, and `SHARE_THIS.txt` (instructions for uploading to GitHub Releases). Enforces clean git worktree, uses `git ls-files` to determine what to package, excludes tests/docs/scripts.

### .github/workflows/ci.yml (~175 lines)
GitHub Actions workflow with four jobs: `test-unix` (matrix: Ubuntu + macOS, Python 3.10/3.12/3.13), `test-windows` (same Python versions), `windows-installer-smoke` (builds release, serves locally, runs real installer), `windows-launcher-smoke` (tests `news-digest.ps1 help`).
