# Command Reference

## Installation

| Command | Platform | Description |
|---------|----------|-------------|
| `curl -fsSL <url>/install.sh \| bash` | macOS/Linux | One-line install (pipe to bash) |
| `curl -fsSLO <url>/install.sh && bash install.sh` | macOS/Linux | Download then run (inspectable) |
| `irm <url>/install.ps1 \| iex` | Windows | One-line install (PowerShell pipe) |
| `iwr <url>/install.ps1 -OutFile install.ps1; powershell -ExecutionPolicy Bypass -File .\install.ps1` | Windows | Download then run |
| `./start.sh` | macOS/Linux | Manual bootstrap (if cloned from git) |

## Daily Usage

| Command | Description |
|---------|-------------|
| `news-digest` | Launch interactive menu (9 options) |
| `venv/bin/python3 main.py` | Send digest directly |
| `venv/bin/python3 main.py --dry-run` | Preview without sending |
| `venv/bin/python3 main.py --force` | Bypass duplicate detection |

### Windows Equivalents

| Command | Description |
|---------|-------------|
| `news-digest` | Launch interactive menu (via .cmd wrapper) |
| `venv\Scripts\python.exe main.py` | Send digest directly |
| `venv\Scripts\python.exe main.py --dry-run` | Preview without sending |
| `venv\Scripts\python.exe main.py --force` | Bypass duplicate detection |

## Development

| Command | Description |
|---------|-------------|
| `venv/bin/python3 -m pytest tests/ -v` | Run full test suite (155+ tests) |
| `venv/bin/python3 -m pytest tests/test_scraper.py -v` | Run specific test file |
| `venv/bin/python3 -m pytest tests/ -k "TestCleanHtml" -v` | Run tests matching pattern |
| `python3 scripts/build_release.py` | Build release artifacts in dist/ |
| `NEWSDIGEST_ALLOW_DIRTY=1 python3 scripts/build_release.py` | Build from dirty worktree |

## Debugging

| Command | Description |
|---------|-------------|
| `cat .env` | View current configuration (contains secrets!) |
| `cat .last_sent` | View last edition hash |
| `cat logs/stdout.log` | View scheduled run output |
| `cat logs/stderr.log` | View scheduled run errors |
| `launchctl list \| grep newsdigest` | Check macOS schedule (macOS) |
| `crontab -l \| grep newsdigest` | Check Linux schedule (Linux) |
| `schtasks /Query /TN "com.newsdigest.daily"` | Check Windows schedule |

## Environment Variables (Testing/CI)

| Variable | Purpose |
|----------|---------|
| `NEWSDIGEST_RELEASE_BASE_URL` | Override download URL for installer |
| `NEWSDIGEST_INSTALL_DIR` | Override install directory |
| `NEWSDIGEST_SKIP_LAUNCH` | Skip launching setup wizard after install |
| `NEWSDIGEST_ALLOW_DIRTY` | Allow build_release.py on dirty worktree |
