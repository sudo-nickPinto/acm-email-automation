# Lesson 09 — Scraper Deep Dive

> **Goal:** Understand every line of `newsdigest/scraper.py` — how
> articles are fetched, parsed, cleaned, and packaged into dataclasses.

---

## 1  Purpose

The scraper is the **data-acquisition layer**.  It turns remote RSS XML
into clean Python objects that the emailer can format.

```
Internet  →  HTTP GET  →  XML bytes  →  ElementTree  →  Article objects
```

---

## 2  Module-Level Setup

```python
import html
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import date
from email.utils import parsedate_to_datetime

import requests

from newsdigest.config import SELECTED_SOURCES
from newsdigest.sources import AVAILABLE_SOURCES, NewsSource, get_source_by_key

REQUEST_TIMEOUT: int = 30
```

**Why each import matters:**

| Import | Role |
|--------|------|
| `html` | `html.unescape()` decodes `&amp;`, `&#8217;`, etc. |
| `re` | Regex-based HTML tag stripping |
| `ET` (ElementTree) | Stdlib XML parser — no external dependency needed |
| `dataclass`, `field` | Structured return types instead of dicts |
| `date` | "Published today?" comparison |
| `parsedate_to_datetime` | RFC 822 date parsing (the format RSS uses) |
| `requests` | HTTP client (only external dependency) |

`REQUEST_TIMEOUT = 30` — if a feed doesn't respond in 30 seconds, the
request is abandoned.  This prevents the script from hanging indefinitely
on a dead server.

---

## 3  Data Models

### 3.1  `Article`

```python
@dataclass
class Article:
    title: str
    description: str
    link: str
    source_name: str
    pub_date: str = ""
```

A flat, immutable-by-convention record.  `pub_date` defaults to `""` because
some RSS feeds omit it.  The field stores the **raw RFC 822 string** from the
feed — parsing only happens when we need a `date` object.

### 3.2  `SourceResult`

```python
@dataclass
class SourceResult:
    source: NewsSource
    articles: list[Article] = field(default_factory=list)
    error: str = ""
    no_new_today: bool = False
```

**Design insight:** `error` being a string (not an exception) means the
caller doesn't have to wrap every call in try/except.  If `error` is
non-empty, the fetch failed.  If `no_new_today` is `True`, the feed had
articles but none published today.

Why `field(default_factory=list)` instead of `articles: list = []`?
Because mutable defaults in dataclasses are shared across all instances —
a classic Python gotcha.  `default_factory` creates a new list per instance.

---

## 4  Date Handling

### 4.1  `_parse_pub_date()`

```python
def _parse_pub_date(pub_date_str: str) -> date | None:
    if not pub_date_str:
        return None
    try:
        dt = parsedate_to_datetime(pub_date_str)
        return dt.astimezone().date()
    except (ValueError, TypeError):
        return None
```

**Line-by-line:**

1. Guard clause — empty strings return `None` (no date available)
2. `parsedate_to_datetime()` handles RFC 822 dates like
   `"Mon, 25 Mar 2026 14:30:00 GMT"` and returns a timezone-aware `datetime`
3. `.astimezone()` converts to the **user's local timezone** — critical
   because a GMT article published at 11 PM might be "today" in New York
   but "tomorrow" in Tokyo
4. `.date()` extracts just the date portion for comparison
5. Catch `ValueError`/`TypeError` for malformed dates — return `None`
   rather than crashing

### 4.2  `_is_published_today()`

```python
def _is_published_today(pub_date_str: str) -> bool:
    pub = _parse_pub_date(pub_date_str)
    if pub is None:
        return False
    return pub == date.today()
```

Simple wrapper.  If we can't parse the date, the article is **not** considered
"today" — this is conservative by design.  We'd rather skip an article than
include one from last week.

---

## 5  HTML Cleaning

```python
def _clean_html(raw_html: str) -> str:
    text = re.sub(r"<img[^>]*>", "", raw_html)       # Remove <img> tags
    text = re.sub(r"<br\s*/?>", "\n", text)           # <br> → newline
    text = re.sub(r"<[^>]+>", "", text)               # Strip all remaining tags
    text = html.unescape(text)                         # &amp; → &
    text = re.sub(r"\n{3,}", "\n\n", text)            # Collapse triple+ newlines
    text = re.sub(r"[ \t]+", " ", text)               # Collapse horizontal whitespace
    return text.strip()
```

**Why not use BeautifulSoup?** Two reasons:

1. **Minimal dependencies** — this is a friends-use project.  Every extra
   package is one more thing that can fail during install.
2. **Speed** — regex tag stripping is ~10x faster than building a DOM tree
   for content we're going to flatten to text anyway.

The order matters:
- Remove `<img>` **before** the generic strip, or the alt text would leak through
- Convert `<br>` to newlines **before** stripping, or line breaks are lost
- `html.unescape()` **after** tag stripping, so we don't decode entities
  inside tags we're about to remove

---

## 6  Fetching a Single Source

```python
def _fetch_single_source(source: NewsSource) -> SourceResult:
```

This is the core function.  Let's trace it step by step:

### Step 1: HTTP GET

```python
response = requests.get(source.rss_url, timeout=REQUEST_TIMEOUT)
response.raise_for_status()
```

`raise_for_status()` throws an `HTTPError` for 4xx/5xx responses.
The timeout prevents hanging on unresponsive servers.

### Step 2: Parse XML

```python
root = ET.fromstring(response.content)
channel = root.find("channel")
```

RSS 2.0 structure: `<rss> → <channel> → <item>*`.  We use
`response.content` (bytes) instead of `response.text` (str) because
ElementTree handles encoding declarations in the XML header itself.

### Step 3: Extract Articles

```python
for item in items[:source.max_articles]:
    title = item.findtext("title", "").strip()
    link = item.findtext("link", "").strip()
    pub_date = item.findtext("pubDate", "").strip()
```

`max_articles` truncation happens here — we never parse more than needed.
`findtext("title", "")` returns `""` if the element is missing, avoiding
`None` handling everywhere.

### Step 4: Description Extraction

```python
desc_raw = item.findtext("description", "")
content_ns = "{http://purl.org/rss/1.0/modules/content/}"
content_encoded = item.findtext(f"{content_ns}encoded", "")
```

**Why two sources?**  RSS feeds vary:
- Most feeds put a summary in `<description>`
- Some feeds (WordPress-based) put full content in `<content:encoded>`
- We prefer `<description>` (shorter, better for a digest summary)
- Fall back to `<content:encoded>` if description is empty

### Step 5: Truncation

```python
if len(description) > 300:
    description = description[:297] + "..."
```

Prevents a single article from dominating the email.

### Step 6: Error Handling

```python
except requests.Timeout:
    return SourceResult(source=source, error=f"Timed out after {REQUEST_TIMEOUT}s")
except requests.HTTPError as e:
    return SourceResult(source=source, error=f"HTTP error: {e.response.status_code}")
except requests.ConnectionError:
    return SourceResult(source=source, error="Connection failed — check your internet")
except ET.ParseError:
    return SourceResult(source=source, error="Failed to parse XML from feed")
```

**Critical design decision:** errors are **captured, not raised**.
Each source fails independently — if BBC is down, we still get NYTimes.

---

## 7  Fetching All Sources

```python
def fetch_all_sources() -> list[SourceResult]:
    results: list[SourceResult] = []
    for key in SELECTED_SOURCES:
        source = get_source_by_key(key)
        if source is None:
            print(f"  Warning: Unknown source key '{key}' in config — skipping")
            continue
        result = _fetch_single_source(source)
        results.append(result)
    return results
```

Linear iteration over the user's chosen sources.  Unknown keys (e.g., after
removing a source from `sources.py`) are warned and skipped, not crashed.

---

## 8  Security Considerations

- **No user input in URLs** — RSS URLs come from the hardcoded source registry
- **Timeout** prevents denial-of-service from slow servers
- **No `eval()`** — XML parsing uses stdlib ElementTree which doesn't execute code
- **Content is cleaned** — HTML tags stripped before display

---

## 9  Key Takeaways

| Concept | Implementation |
|---------|---------------|
| Fail soft, fail independently | Errors captured in `SourceResult.error` |
| Parse only what you need | `max_articles` truncation at parse time |
| Timezone-aware dates | `astimezone()` before `date()` comparison |
| Minimal dependencies | stdlib XML + regex over BeautifulSoup |
| Clean data at the boundary | `_clean_html()` strips tags before storage |
