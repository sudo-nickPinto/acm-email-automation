# Lesson 04 — Architecture and Data Flow

## The big picture

News Digest is structured as a **pipeline** — data flows through a series of stages, each handled by a single module. Every module has exactly one job, and the modules communicate through well-defined data structures (dataclasses).

```
User's .env file
      |
      v
config.py (loads settings)
      |
      v
sources.py (resolves source keys to NewsSource objects)
      |
      v
scraper.py (HTTP GET -> XML parse -> list[Article])
      |
      v
main.py (filters today's articles, deduplicates)
      |
      v
emailer.py (formats HTML + plain text, sends via SMTP)
      |
      v
Gmail inbox
```

## Why a pipeline?

A pipeline architecture has several advantages for this project:

1. **Each stage is independently testable** — you can test the scraper without sending emails, and test the emailer without hitting the network
2. **Failure isolation** — if one newspaper's RSS feed is down, the others still get fetched and sent
3. **Simple mental model** — data flows in one direction, so you can trace any bug by following the flow

## The three layers

The codebase has three conceptual layers:

### Layer 1: Installation and setup
These files run once (during installation) and then are rarely touched again:

| File | Purpose | Runs when |
|------|---------|-----------|
| `install.sh` / `install.ps1` | Download, verify, extract | User first installs |
| `start.sh` | Create venv, install deps | User first installs or re-runs setup |
| `setup_wizard.py` | Collect user preferences | User first installs or re-runs setup |

### Layer 2: Core runtime
These files run every time a digest is sent:

| File | Purpose | Runs when |
|------|---------|-----------|
| `config.py` | Load `.env` settings | Every import of the package |
| `sources.py` | Provide feed metadata | Every fetch operation |
| `scraper.py` | Fetch and parse RSS | Every digest send |
| `emailer.py` | Format and send email | Every digest send |
| `main.py` | Orchestrate the pipeline | Every digest send |

### Layer 3: Management and operations
These files handle ongoing maintenance:

| File | Purpose | Runs when |
|------|---------|-----------|
| `cli.py` | Interactive menu | User runs `news-digest` |
| `scheduler.py` | Schedule install/remove | User changes schedule settings |
| `paths.py` | Cross-platform paths | Imported by cli.py, scheduler.py, setup_wizard.py |

## Data structures

The pipeline passes data between stages using three key dataclasses:

### NewsSource (defined in sources.py)
Represents the metadata about a single newspaper feed:
```python
@dataclass
class NewsSource:
    key: str            # "bbc_tech" — stored in .env
    name: str           # "BBC News — Technology" — shown to users
    description: str    # One-line description for the wizard
    rss_url: str        # URL to the RSS feed
    max_articles: int   # How many articles to include (default: 5)
```

**Why a dataclass?** A dictionary like `{"name": "BBC", "url": "..."}` has no typo protection. If you write `source["nmae"]` instead of `source["name"]`, Python will not catch the bug until runtime — and only if that code path executes. A dataclass catches this immediately with an `AttributeError`, and your IDE can autocomplete field names.

### Article (defined in scraper.py)
Represents a single parsed article:
```python
@dataclass
class Article:
    title: str          # "AI Breakthrough at Stanford"
    description: str    # Cleaned plain-text blurb
    link: str           # "https://example.com/article"
    source_name: str    # "MIT Technology Review"
    pub_date: str       # "Tue, 25 Mar 2025 12:00:00 GMT"
```

### SourceResult (defined in scraper.py)
Container grouping all articles from one source, plus error info:
```python
@dataclass
class SourceResult:
    source: NewsSource          # The feed metadata
    articles: list[Article]     # Parsed articles (may be empty)
    error: str = ""             # Error message if fetch failed
    no_new_today: bool = False  # True if feed has articles but none today
```

**Why `no_new_today`?** A source might have articles in its feed, but none published today. This is different from "the feed is empty" and different from "the fetch failed." The emailer shows a friendly "No new articles published today" message instead of silently omitting the source.

## Import graph

Understanding what imports what helps you see the dependency structure:

```
main.py
  |-- newsdigest.scraper (fetch_all_sources, SourceResult, _is_published_today)
  |-- newsdigest.emailer (send_email, build_plain_text)
  |-- newsdigest.config  (SELECTED_SOURCES)

newsdigest.scraper
  |-- newsdigest.config  (SELECTED_SOURCES)
  |-- newsdigest.sources (AVAILABLE_SOURCES, NewsSource, get_source_by_key)

newsdigest.emailer
  |-- newsdigest.config  (SMTP settings)
  |-- newsdigest.scraper (Article, SourceResult — types only)

newsdigest.cli
  |-- newsdigest.paths   (venv_python_path)
  |-- newsdigest.sources (AVAILABLE_SOURCES — for source picker)
  |-- newsdigest.scheduler (schedule management)

newsdigest.scheduler
  |-- newsdigest.paths   (venv_python_path)

setup_wizard.py
  |-- newsdigest.sources   (AVAILABLE_SOURCES)
  |-- newsdigest.scheduler (install_schedule, etc.)
  |-- newsdigest.paths     (is_windows, venv_python_path)
```

**Key observation:** `config.py` is at the bottom of the dependency tree. It is imported by `scraper.py` and `emailer.py`, which means `.env` must be present and valid before any runtime operation.

## Error handling philosophy

Errors in this pipeline are handled differently at each stage:

- **scraper.py** — Never raises exceptions. Errors are captured in `SourceResult.error`. This means one failing source does not crash the whole run.
- **emailer.py** — Lets SMTP exceptions propagate. If the email cannot be sent, the user should know immediately.
- **main.py** — Checks for empty results and exits with `sys.exit(1)` and a clear message. This is the "fail fast, fail loud" principle.
- **cli.py** — Catches most exceptions and displays them as friendly warnings, because the interactive menu should not crash.
