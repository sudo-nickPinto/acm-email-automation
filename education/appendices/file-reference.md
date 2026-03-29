# File Reference

## Root Files

| File | Purpose | Lines |
|------|---------|-------|
| `main.py` | Orchestrator: fetch → filter → dedup → send | ~155 |
| `setup_wizard.py` | Interactive 5-step setup (sources, email, password, schedule, test) | ~570 |
| `start.sh` | Bootstrap: installs Python, creates venv, launches wizard | ~200 |
| `install.sh` | macOS/Linux one-line installer (curl \| bash) | ~270 |
| `install.ps1` | Windows one-line installer (irm \| iex) | ~320 |
| `news-digest` | Bash CLI wrapper (symlinked to /usr/local/bin) | ~115 |
| `news-digest.ps1` | PowerShell CLI wrapper (Windows equivalent) | ~130 |
| `requirements.txt` | Python dependencies (requests, python-dotenv, pytest) | ~5 |
| `README.md` | Public-facing quickstart documentation | — |

## Core Package (`newsdigest/`)

| File | Purpose | Lines |
|------|---------|-------|
| `__init__.py` | Package marker with docstring | ~5 |
| `config.py` | Loads `.env`, exposes settings as module constants | ~75 |
| `sources.py` | `NewsSource` dataclass + `AVAILABLE_SOURCES` registry | ~100 |
| `scraper.py` | RSS fetching, XML parsing, HTML cleaning | ~250 |
| `emailer.py` | Plain-text + HTML email formatting, SMTP sending | ~300 |
| `cli.py` | 9-option interactive menu for post-install management | ~660 |
| `scheduler.py` | Daily schedule install/uninstall (macOS/Linux/Windows) | ~400 |
| `paths.py` | Cross-platform venv path helpers | ~30 |

## Scripts (`scripts/`)

| File | Purpose | Lines |
|------|---------|-------|
| `build_release.py` | Builds dist/ with zip, checksums, installers | ~180 |

## Tests (`tests/`)

| File | Tests | Lines |
|------|-------|-------|
| `conftest.py` | Shared fixtures (sample sources, articles, RSS XML) | ~112 |
| `test_scraper.py` | HTML cleaning, XML parsing, error handling | ~282 |
| `test_emailer.py` | Email formatting, HTML escaping, URL validation | ~296 |
| `test_main.py` | Dedup, state files, CLI flags, article filtering | ~235 |
| `test_cli.py` | Menu dispatch, env manipulation, uninstall flow | ~405 |
| `test_scheduler.py` | LaunchAgent, cron, schtasks mocking | ~180 |
| `test_config.py` | Environment variable parsing | ~86 |
| `test_sources.py` | Source lookup, key uniqueness | ~75 |
| `test_paths.py` | Cross-platform path helpers | ~30 |
| `test_install_sh.py` | Bash installer structure analysis | ~136 |
| `test_install_ps1.py` | PowerShell installer structure analysis | ~135 |
| `test_build_release.py` | File exclusion, zip contents, checksums | ~134 |

## Generated Files (not in git)

| File | Purpose |
|------|---------|
| `.env` | User credentials and settings (written by wizard) |
| `.last_sent` | SHA-256 hash of last sent edition |
| `venv/` | Python virtual environment |
| `logs/` | Stdout/stderr from scheduled runs |
| `dist/` | Release build output |

## CI (`.github/workflows/`)

| File | Purpose |
|------|---------|
| `ci.yml` | Cross-platform test matrix (macOS/Linux/Windows × Python 3.10/3.12/3.13) |
