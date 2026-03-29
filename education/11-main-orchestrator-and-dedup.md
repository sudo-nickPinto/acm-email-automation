# Lesson 11 — Main Orchestrator and Deduplication

> **Goal:** Understand how `main.py` ties the scraper and emailer
> together, filters articles to today, and prevents duplicate sends.

---

## 1  Purpose

`main.py` is the **orchestrator** — the single entry point that
coordinates the entire pipeline:

```
CLI flags  →  fetch  →  filter to today  →  dedup check  →  send/preview
```

At ~155 lines, it's intentionally thin.  The heavy lifting is delegated
to the scraper and emailer modules.

---

## 2  Module Setup

```python
import hashlib
import sys
from datetime import date
from pathlib import Path

from newsdigest.scraper import fetch_all_sources, SourceResult, _is_published_today
from newsdigest.emailer import send_email, build_plain_text
from newsdigest.config import SELECTED_SOURCES

STATE_FILE = Path(__file__).parent / ".last_sent"
```

`STATE_FILE` (`.last_sent`) stores the SHA-256 hash of the last edition
we sent.  It lives in the project root alongside `main.py`.

---

## 3  Deduplication System

### 3.1  Hashing the Edition

```python
def _results_hash(results: list[SourceResult]) -> str:
    all_titles = []
    for result in results:
        for article in result.articles:
            all_titles.append(article.title)
    combined = f"{date.today().isoformat()}|" + "|".join(all_titles)
    return hashlib.sha256(combined.encode()).hexdigest()
```

The hash includes:
- **Today's date** — so the same articles on different days produce
  different hashes (user hears about an update daily if it persists)
- **All article titles** — article-level granularity
- **Pipe-delimited** — prevents title concatenation collisions

**Why SHA-256?**  Overkill for dedup, but it's stdlib (`hashlib`) and
produces a fixed-length, collision-resistant fingerprint.

### 3.2  Check and Save

```python
def _already_sent(current_hash: str) -> bool:
    if not STATE_FILE.exists():
        return False
    stored = STATE_FILE.read_text().strip()
    return stored == current_hash

def _save_state(current_hash: str) -> None:
    STATE_FILE.write_text(current_hash)
```

The state file is a single line: the hex digest.  No JSON, no database,
no dependencies — just a text file.

---

## 4  Main Flow

```python
def main():
    force = "--force" in sys.argv
    dry_run = "--dry-run" in sys.argv
```

### Step 1: Validate Configuration

```python
if not SELECTED_SOURCES:
    print("No news sources configured.")
    print("Run ./start.sh to set up your digest.")
    sys.exit(1)
```

Fail fast if the user hasn't run the setup wizard yet.

### Step 2: Fetch All Sources

```python
results = fetch_all_sources()
```

This calls the scraper's main function, which returns a list of
`SourceResult` objects (one per source, potentially with errors).

### Step 3: Filter to Today

```python
for result in results:
    if result.error:
        continue
    fresh = [a for a in result.articles if _is_published_today(a.pub_date)]
    if not fresh and result.articles:
        result.no_new_today = True
    result.articles = fresh
```

**Why filter here instead of in the scraper?**  Separation of concerns.
The scraper's job is to fetch and parse.  The orchestrator decides
business logic like "only today's articles."

The `no_new_today` flag is set when a source had articles but none were
fresh — this lets the emailer show "No new articles published today"
instead of silently omitting the source.

### Step 4: Count and Validate

```python
total = sum(len(r.articles) for r in results)
errors = sum(1 for r in results if r.error)
stale = sum(1 for r in results if r.no_new_today)
valid_sources = len(results) - errors
```

If there are zero articles and zero stale sources, exit — there's nothing
to send.  But if there are stale sources, we still send (the email shows
"no new articles today" for those sources).

### Step 5: Dedup Check

```python
current_hash = _results_hash(results)
if not force and _already_sent(current_hash):
    print("Already sent this digest. No new articles since last send.")
    sys.exit(0)
```

`--force` bypasses dedup entirely.

### Step 6: Send or Preview

```python
if dry_run:
    print(build_plain_text(results))
    return  # Don't save state for dry runs

send_email(results)
_save_state(current_hash)
```

**Dry runs don't save state** — so you can preview multiple times without
blocking the real send.  State is only saved after a successful email send.

---

## 5  CLI Flags

| Flag | Effect |
|------|--------|
| `--dry-run` | Print plain-text preview, skip send, don't save state |
| `--force` | Bypass dedup check, send even if already sent today |
| (none) | Normal mode: fetch, dedup, send, save state |

---

## 6  Error Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success / already sent (not an error) |
| `1` | No sources configured or no articles found |

---

## 7  Key Takeaways

| Concept | Implementation |
|---------|---------------|
| Thin orchestrator | Delegates to scraper + emailer modules |
| Content-based dedup | SHA-256 hash of date + titles |
| File-based state | `.last_sent` — single line, no dependencies |
| Today-only filtering | `_is_published_today()` at the orchestrator level |
| Dry-run safety | Previews don't save state |
