# 07 — Main Orchestrator

## What This Module Does

`main.py` is the file you actually run. It coordinates the scraper and emailer in a simple pipeline:

```
Validate config  →  Fetch all sources  →  Check for duplicates  →  Send email (or preview)
```

It contains no scraping logic. It contains no email formatting logic. Its only job is to decide **what** to do and call the right functions in the right order.

## Why Keep the Orchestrator Thin?

1. **Readability** — a monolithic file with scraping, email formatting, and orchestration is hard to navigate. Focused modules are easier.
2. **Testability** — you can test the scraper independently by running `venv/bin/python3 -m newsdigest.scraper`. A monolith makes isolated testing impossible.
3. **Maintenance** — when a feed changes format, you open `scraper.py`. When you want to restyle the email, you open `emailer.py`. You don't wade through unrelated code.

## Walkthrough

### Imports

```python
import hashlib
import sys
from pathlib import Path

from newsdigest.scraper import fetch_all_sources, SourceResult
from newsdigest.emailer import send_email, build_plain_text
from newsdigest.config import SELECTED_SOURCES
```

All business logic is imported from the `newsdigest` package. The orchestrator only uses stdlib for its own logic (hashing, command-line args, file paths).

### State File

```python
STATE_FILE = Path(__file__).parent / ".last_sent"
```

- `__file__` — path to the current script
- `Path(__file__).parent` — the directory containing the script
- `/ ".last_sent"` — join with the filename

Result: `/path/to/project/.last_sent`

### Duplicate Detection

```python
def _results_hash(results: list[SourceResult]) -> str:
    all_titles = []
    for result in results:
        for article in result.articles:
            all_titles.append(article.title)

    combined = "|".join(all_titles)
    return hashlib.sha256(combined.encode()).hexdigest()
```

This function fingerprints the current set of articles across all sources:

1. Collect all article titles from all sources
2. Join them with `|` separators (prevents `["AB", "CD"]` and `["A", "BCD"]` from hashing identically)
3. SHA-256 hash → 64-character hex string

**Why titles only?** Titles are the most stable identifier. Descriptions might have minor formatting differences between fetches, but titles stay the same within an edition.

```python
def _already_sent(current_hash: str) -> bool:
    if not STATE_FILE.exists():
        return False
    stored = STATE_FILE.read_text().strip()
    return stored == current_hash
```

If `.last_sent` doesn't exist, we've never sent anything. Otherwise, compare the stored hash with the current one.

### The Main Function

```python
def main():
    force = "--force" in sys.argv
    dry_run = "--dry-run" in sys.argv
```

Parse command-line flags from `sys.argv`. For two boolean flags, checking `sys.argv` directly is simpler than using `argparse`.

```python
    if not SELECTED_SOURCES:
        print("No news sources configured.")
        print("Run ./start.sh to set up your digest.")
        sys.exit(1)
```

Guard clause: if the user hasn't run the setup wizard yet, stop immediately with a helpful message.

```python
    results = fetch_all_sources()
    total = sum(len(r.articles) for r in results)
    errors = sum(1 for r in results if r.error)

    if total == 0:
        print("No articles found from any source.")
        sys.exit(1)
```

Fetch from all sources. If every source returned zero articles (or all failed), exit with an error. Otherwise continue even if some sources had errors — partial results are better than nothing.

```python
    current_hash = _results_hash(results)

    if not force and _already_sent(current_hash):
        print("Already sent this digest. No new articles since last send.")
        sys.exit(0)
```

Duplicate check. Exit code 0 because skipping a duplicate is not an error. The `--force` flag bypasses this check.

```python
    if dry_run:
        print(build_plain_text(results))
        return
```

Dry run mode: print the email to the terminal without sending. Dry runs don't save state — a preview shouldn't mark the edition as "sent."

```python
    send_email(results)
    _save_state(current_hash)
    print("Done!")
```

The happy path: send the email, then save the hash. The order matters — if `send_email()` raises an exception, we don't save state, so the next run will try again.

### The `if __name__` Guard

```python
if __name__ == "__main__":
    main()
```

When you run `python main.py`, `__name__` is `"__main__"`. When you `import main`, `__name__` is `"main"`. The guard ensures `main()` only runs when executed directly.

## CLI Flags

| Flag | Behavior |
|------|----------|
| (none) | Fetch, deduplicate, send |
| `--dry-run` | Fetch, print plain-text preview, don't send or save state |
| `--force` | Fetch, skip duplicate check, send |
| `--force --dry-run` | Fetch, print preview (force has no effect on dry runs) |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success (email sent, or duplicate detected and skipped) |
| 1 | Error (no sources configured, no articles found) |

---

**Previous:** [06 — Emailer Deep Dive](06-emailer-deep-dive.md)
**Next:** [08 — Automation and Scheduling](08-automation-and-scheduling.md)
