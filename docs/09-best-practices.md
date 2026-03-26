# 09 — Best Practices (Lessons from This Project)

This document explains the software engineering principles demonstrated in this project. These are concepts you'll encounter in any professional codebase.

---

## 1. Separation of Concerns

**Principle:** Each module should have one reason to change.

| Module | Reason to change |
|--------|-----------------|
| `sources.py` | A newspaper changes its RSS URL, or we add a new source |
| `scraper.py` | A feed changes its XML format |
| `emailer.py` | We want to restyle the email or switch SMTP providers |
| `config.py` | We change how configuration is loaded |
| `setup_wizard.py` | We change the setup flow or add new prompts |
| `main.py` | We change orchestration logic (e.g., add retry logic) |

**Real-world example:** To add a new newspaper, you only touch `sources.py`. The scraper, emailer, wizard, and orchestrator all adapt automatically because they read from the source registry.

---

## 2. Don't Repeat Yourself (DRY)

Configuration values are defined once in `config.py` and imported everywhere. Source metadata lives once in `sources.py` and is referenced by the wizard, scraper, and emailer:

```python
# GOOD — single source of truth
# sources.py
AVAILABLE_SOURCES = [
    NewsSource(key="bbc_tech", name="BBC News — Technology", ...),
]

# wizard uses it for the selection menu
# scraper uses it for the RSS URL
# emailer uses the name for section headers
```

---

## 3. Fail Fast, Fail Loud

The project avoids catching exceptions silently:

```python
# GOOD — loud failure at the pipeline level
response.raise_for_status()  # Raises on HTTP errors

# BAD — silent failure
try:
    response.raise_for_status()
except:
    pass  # Error swallowed, program continues with bad data
```

The exception to this rule is at the **source level** — individual feed failures are captured in `SourceResult.error` so that one broken feed doesn't crash the entire digest. This is intentional and documented.

---

## 4. Idempotency

**Definition:** An operation is idempotent if running it multiple times produces the same result as running it once.

This project is idempotent:
- Running `main.py` twice for the same articles → second run detects the duplicate and exits cleanly
- Running `./start.sh` twice → checks if venv exists, re-installs deps (harmless), asks to keep or reconfigure

---

## 5. Environment Variables for Secrets

**Never commit secrets to git.**

```gitignore
# .gitignore
.env
.last_sent
venv/
__pycache__/
```

The pattern:
1. `.env.example` — committed to git, shows **what** variables are needed
2. `.env` — git-ignored, contains **actual** secrets (written by the setup wizard)
3. `config.py` — reads `.env` at import time, exposes constants

In the live setup flow, `.env` is also written with restrictive POSIX permissions so the secrets are only readable by the current user.

The installer follows the same philosophy: release assets are verified with `SHA256SUMS.txt` before extraction, which helps catch accidental corruption and mismatched artifacts. That does not independently authenticate the release origin, so the GitHub release channel is still a trust boundary today. Signed artifacts are still a good future hardening step.

---

## 6. Defensive Coding

### Guard clauses

```python
# Guard clauses flatten the logic and exit early on errors
def main():
    if not SELECTED_SOURCES:
        sys.exit(1)

    results = fetch_all_sources()

    if total == 0:
        sys.exit(1)

    if _already_sent(current_hash):
        sys.exit(0)

    send_email(results)
    _save_state(current_hash)
```

Check for error conditions at the top and exit early. This keeps the happy path at the left margin with no deep nesting.

### Timeouts

```python
response = requests.get(source.rss_url, timeout=REQUEST_TIMEOUT)
```

Always set timeouts on network calls. Without a timeout, a hung server blocks the script forever.

### Default values

```python
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL", os.getenv("SMTP_EMAIL"))
title = item.findtext("title", "").strip()
```

Providing defaults prevents `None` values from propagating through the code.

---

## 7. The `if __name__ == "__main__"` Pattern

```python
if __name__ == "__main__":
    main()
```

Allows files to serve dual purposes:
- **As a module** (imported) → the block is skipped
- **As a script** (run directly) → the block executes

The scraper module uses this for standalone testing — running `python -m newsdigest.scraper` prints the fetched articles.

---

## 8. Meaningful Naming

Good names make code self-documenting:

| Name | What it tells you |
|------|------------------|
| `fetch_all_sources()` | Fetches from all sources |
| `send_email(results)` | Sends an email with results |
| `_clean_html(raw_html)` | Cleans HTML; underscore means internal |
| `_already_sent(hash)` | Checks if something was already sent |
| `get_source_by_key(key)` | Looks up a source by its key |
| `SELECTED_SOURCES` | All caps = constant; the user's selected sources |
| `REQUEST_TIMEOUT` | How long to wait for a request |

---

## 9. Graceful Degradation

The scraper is designed to degrade gracefully when things go wrong:

```python
if result.error:
    # Show a warning in the email, continue with other sources
else:
    # Include this source's articles
```

If BBC's server is down but ACM and NYTimes work fine, the user still gets a useful digest with a small warning about BBC. This is better than sending nothing.

---

## 10. Extensibility Through Data

Adding a new newspaper source requires adding one entry to a list in `sources.py`:

```python
NewsSource(
    key="new_source",
    name="New Newspaper",
    description="A brief description for the wizard",
    rss_url="https://example.com/rss",
    max_articles=5,
)
```

No new code paths, no new conditionals, no changes to any other file. The system is data-driven — the behavior adapts to what's in the registry.

---

**Previous:** [08 — Bootstrap and Setup](08-automation-and-scheduling.md)
**Next:** [10 — Troubleshooting](10-troubleshooting.md)
