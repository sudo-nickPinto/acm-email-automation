# Lesson 08 — Source Registry and Config

## sources.py — The newspaper registry

This module defines every newspaper source available in the digest. It is the simplest module in the project and demonstrates several important design patterns.

### The NewsSource dataclass

```python
from dataclasses import dataclass

@dataclass
class NewsSource:
    key: str            # Short unique ID stored in .env (e.g., "bbc_tech")
    name: str           # Human-readable display name
    description: str    # One-line description for the wizard
    rss_url: str        # URL to the RSS/XML feed
    max_articles: int = 5  # Default limit per source
```

**What is a dataclass?** Python's `@dataclass` decorator automatically generates `__init__`, `__repr__`, and `__eq__` methods from the field declarations. You write the data structure, Python writes the boilerplate.

Without `@dataclass`, you would need:
```python
class NewsSource:
    def __init__(self, key, name, description, rss_url, max_articles=5):
        self.key = key
        self.name = name
        self.description = description
        self.rss_url = rss_url
        self.max_articles = max_articles
```

The dataclass version is shorter, less error-prone, and self-documenting.

### The source registry

```python
AVAILABLE_SOURCES: list[NewsSource] = [
    NewsSource(
        key="acm_technews",
        name="ACM TechNews",
        description="Curated computing & technology articles from ACM (Mon/Wed/Fri)",
        rss_url="https://news.content.smithbucklin.com/acm/TechNews_rss.xml",
        max_articles=10,
    ),
    NewsSource(
        key="mit_tech_review",
        name="MIT Technology Review",
        description="Emerging technology analysis from MIT",
        rss_url="https://www.technologyreview.com/feed/",
        max_articles=5,
    ),
    NewsSource(
        key="nytimes_tech",
        name="The New York Times — Technology",
        description="Technology coverage from the NYTimes",
        rss_url="https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
        max_articles=5,
    ),
    NewsSource(
        key="bbc_tech",
        name="BBC News — Technology",
        description="Technology news from the BBC",
        rss_url="https://feeds.bbci.co.uk/news/technology/rss.xml",
        max_articles=5,
    ),
]
```

**Why is ACM max_articles=10 while others are 5?** ACM TechNews publishes a curated digest only on Monday/Wednesday/Friday, so its articles are already filtered. The other sources publish many articles per day, so 5 prevents the email from becoming too long.

### The lookup function

```python
def get_source_by_key(key: str) -> NewsSource | None:
    for source in AVAILABLE_SOURCES:
        if source.key == key:
            return source
    return None
```

**Why linear search?** With only 4 sources, a dictionary lookup (`SOURCES_BY_KEY = {s.key: s for s in AVAILABLE_SOURCES}`) would add complexity with no measurable performance benefit. Linear search through 4 items is effectively instant.

**Why return None instead of raising?** The caller (scraper.py) handles unknown keys gracefully by printing a warning and skipping. This makes the system resilient to stale `.env` files that reference a source that was later removed from the registry.

### How to add a new source

This is the extension point for the entire project. To add a newspaper:

1. Find its RSS feed URL (look for an RSS/XML icon on the newspaper's website, or search for "newspaper name RSS feed")
2. Add a `NewsSource(...)` to `AVAILABLE_SOURCES`
3. That is it — the wizard, scraper, and emailer all pick it up automatically

This works because:
- The wizard iterates `AVAILABLE_SOURCES` to show the numbered list
- The scraper iterates `SELECTED_SOURCES` (keys stored in `.env`) and resolves each through `get_source_by_key()`
- The emailer receives `list[SourceResult]` (already fetched) and formats whatever it gets

No other file needs to change.

## config.py — Loading settings

### The load sequence

```python
import os
from dotenv import load_dotenv

load_dotenv()  # Reads .env into os.environ
```

**What does `load_dotenv()` do?** It reads the `.env` file line by line, parses `KEY=VALUE` pairs, and injects them into `os.environ`. After this call, `os.getenv("SMTP_EMAIL")` returns the value from `.env` as if it were a real environment variable.

**Why not just read the file directly?** `python-dotenv` handles edge cases: comments (lines starting with `#`), quoted values, missing files (returns gracefully), and `.env` files in parent directories. Using a battle-tested library avoids reimplementing this parsing logic.

### The settings

```python
# SMTP settings
SMTP_EMAIL: str | None = os.getenv("SMTP_EMAIL")
SMTP_APP_PASSWORD: str | None = os.getenv("SMTP_APP_PASSWORD")
SMTP_SERVER: str = "smtp.gmail.com"
SMTP_PORT: int = 587

# Recipient (defaults to sender)
RECIPIENT_EMAIL: str | None = os.getenv("RECIPIENT_EMAIL", os.getenv("SMTP_EMAIL"))

# Source selection
SELECTED_SOURCES_RAW: str = os.getenv("SELECTED_SOURCES", "")
SELECTED_SOURCES: list[str] = [
    s.strip() for s in SELECTED_SOURCES_RAW.split(",") if s.strip()
]

# Schedule
SCHEDULE_TIME: str = os.getenv("SCHEDULE_TIME", "")
```

**Why `str | None`?** The `|` union type (Python 3.10+) means the value could be a string or `None`. `os.getenv()` returns `None` if the key is not set and no default is provided. The type hint documents this possibility.

**Why port 587?** Port 587 is the standard SMTP submission port that uses STARTTLS — it starts as an unencrypted connection, then upgrades to TLS. This is more compatible than port 465 (implicit TLS) across different network configurations.

**How is SELECTED_SOURCES parsed?** The `.env` stores sources as a comma-separated string: `SELECTED_SOURCES=acm_technews,bbc_tech`. The list comprehension splits on commas, strips whitespace, and filters out empty strings. This handles edge cases like trailing commas or extra spaces.

### Module-level constants

These settings are module-level constants, not a class or configuration object. This means they are evaluated once when `config.py` is first imported, and every subsequent import gets the same cached values.

**Implication for the CLI:** When the user changes a setting through the interactive menu, the `.env` file changes on disk, but the already-imported `config` module still holds the old values. That is why `cli.py` has a `_reload_config()` function that clears the cached environment variables and calls `importlib.reload(newsdigest.config)`.
