# 02 — System Design

## Architecture Pattern: Pipeline

This project follows a **pipeline architecture** (also called "pipes and filters"). Data flows in one direction through discrete stages:

```
[Internet]  →  [Scraper]  →  [Orchestrator]  →  [Emailer]  →  [Gmail]  →  [Inbox]
(RSS feeds)   (parse XML)   (deduplicate)     (format)      (SMTP)
```

Each stage does exactly one thing, takes input from the previous stage, and passes output to the next.

### Why a pipeline?

- **Testability** — you can test the scraper without sending email, and test the emailer without hitting the network
- **Replaceability** — swap Gmail for SendGrid by only changing `emailer.py`
- **Debuggability** — if something breaks, you know exactly which stage failed

## Module Dependency Graph

```
start.sh
  └── setup_wizard.py
        └── newsdigest.sources          (reads available sources for the picker)

main.py
  ├── newsdigest.scraper
  │     ├── newsdigest.config           (imports SELECTED_SOURCES)
  │     └── newsdigest.sources          (imports NewsSource, get_source_by_key)
  └── newsdigest.emailer
        ├── newsdigest.config           (imports SMTP_*, RECIPIENT_EMAIL)
        └── newsdigest.scraper          (imports Article, SourceResult for type hints)

newsdigest.config
  └── .env                              (reads secrets via python-dotenv)

newsdigest.sources
  └── (no dependencies — standalone registry)
```

Dependencies only flow downward. There are no circular imports. `sources.py` is a leaf node with zero dependencies — any module can import from it safely.

## Data Model

### `NewsSource` (defined in `sources.py`)

```python
@dataclass
class NewsSource:
    key: str            # "bbc_tech"
    name: str           # "BBC News — Technology"
    description: str    # Shown during setup wizard
    rss_url: str        # URL to the RSS feed
    max_articles: int   # Cap per source (default 5)
```

This represents a newspaper that _could_ be subscribed to. The full registry of available sources lives in `AVAILABLE_SOURCES`.

### `Article` (defined in `scraper.py`)

```python
@dataclass
class Article:
    title: str          # "AI Helps Detect Cancer Earlier"
    description: str    # Plain-text summary
    link: str           # URL to the full article
    source_name: str    # "BBC News — Technology"
    pub_date: str       # Publication date string from the feed
```

This represents a single news article from any source. The scraper returns lists of these.

### `SourceResult` (defined in `scraper.py`)

```python
@dataclass
class SourceResult:
    source: NewsSource          # Which newspaper this came from
    articles: list[Article]     # The articles we parsed
    error: str                  # Error message (empty string if OK)
```

This is the per-source container. It groups articles by their source, and captures errors without crashing so one broken feed doesn't kill the entire run.

### Why dataclasses instead of dictionaries?

| Feature | `dict` | `dataclass` |
|---------|--------|-------------|
| Access | `a["title"]` | `a.title` |
| Typos | Silent `KeyError` at runtime | Caught by IDE/linter |
| Autocomplete | No | Yes |
| `__repr__` | Ugly | Clean |
| Type checking | No | Yes |

## State Management

The project needs to remember one thing between runs: "Have I already sent an email with these exact articles?"

### Approach: File-based hashing

```
All articles across all sources
  → join titles with "|"
  → SHA-256 hash
  → store in .last_sent (64-character hex string)
```

On the next run:
1. Fetch articles from all selected sources
2. Hash all the titles
3. Read `.last_sent`
4. If hashes match → skip (already sent this edition)
5. If different → send email, overwrite `.last_sent`

### Why SHA-256?

- **Deterministic** — same input always produces the same output
- **Fixed size** — always 64 hex characters regardless of input length
- **Collision-resistant** — effectively impossible for two different inputs to produce the same hash

### Why a flat file instead of a database?

The state is a single 64-character string. A database would be massive overkill. A flat file is zero dependencies, human-readable (`cat .last_sent`), and trivially debuggable.

## Multi-Source Design

The key architectural difference from v1 is multi-source support. Here's how it flows:

```
SELECTED_SOURCES (from .env)
  │
  ├── "acm_technews" → get_source_by_key() → NewsSource → HTTP GET → SourceResult
  ├── "nytimes_tech" → get_source_by_key() → NewsSource → HTTP GET → SourceResult
  └── "bbc_tech"     → get_source_by_key() → NewsSource → HTTP GET → SourceResult
                                                                  │
                                                    list[SourceResult]
                                                                  │
                                                          ┌───────┴───────┐
                                                          │  emailer.py   │
                                                          │  One section  │
                                                          │  per source   │
                                                          └───────────────┘
```

Each source is fetched independently. If one feed is down, the others still work — the broken source shows an error message in the email instead of crashing the whole run.

## Email Architecture

The email is a **MIME multipart/alternative** message:

```
Email Message
├── text/plain   ← for terminal email clients, screen readers, --dry-run
└── text/html    ← for Gmail, Outlook, Apple Mail (preferred by clients)
```

Both versions organize articles by source. The HTML version uses colored section headers (one color per newspaper) for visual scanning. The plain-text version uses separator lines.

### Why both formats?

1. **Accessibility** — screen readers work better with plain text
2. **Spam filtering** — emails without a plain-text part score higher on spam tests
3. **Developer convenience** — `--dry-run` prints the plain-text version to the terminal

## Security Considerations

| Concern | Mitigation |
|---------|------------|
| Gmail password in code | Stored in `.env`, git-ignored via `.gitignore` |
| App Password vs. real password | App Passwords are scoped and revocable |
| TLS for SMTP | `starttls()` encrypts the connection before login |
| RSS feed injection | HTML tags are stripped from descriptions via regex |
| Secret in wizard input | Password echoed to terminal during input (limitation of basic `input()`) |

The `.env` file should **never** be committed to git. The `.env.example` file shows what variables are needed without revealing actual values.

## Error Handling Philosophy

This project follows a "fail loudly" approach for the pipeline, but a "capture and continue" approach for individual sources:

- **Pipeline level:** If no articles are found from any source, `main.py` exits with code 1. If SMTP authentication fails, the exception propagates naturally.
- **Source level:** If one RSS feed times out or returns a 404, that source's `SourceResult` has an error message, but the other sources still work. The error appears in the email as a warning banner.

---

**Previous:** [01 — Project Overview](01-project-overview.md)
**Next:** [03 — Stack Rationale](03-stack-rationale.md)
