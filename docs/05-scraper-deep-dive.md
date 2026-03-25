# 05 — Scraper Deep Dive

## What This Module Does

`scraper.py` is responsible for reaching out to one or more newspaper RSS feeds over the internet, downloading the XML data, and converting it into clean lists of `Article` objects grouped by source.

It answers the question: "What are today's articles from each newspaper I subscribed to?"

## Big Picture Flow

```
config.SELECTED_SOURCES        scraper.py                        Return to caller
──────────────────────────────────────────────────────────────────────────────────
["acm_technews",         for each key:
 "bbc_tech"]          →  get_source_by_key(key) → NewsSource
                         HTTP GET to rss_url    → raw XML bytes
                         ET.fromstring(bytes)   → XML tree
                         findall("item")        → XML elements
                         _clean_html(desc)      → plain text
                         build Article objects   → list[Article]
                         wrap in SourceResult    → SourceResult
                                                              list[SourceResult] →
```

## Data Structures

### The `Article` Dataclass

```python
@dataclass
class Article:
    title: str          # Headline
    description: str    # Clean plain-text summary
    link: str           # URL to full article
    source_name: str    # Human-readable newspaper name
    pub_date: str = ""  # Publication date (optional, from feed)
```

This is the universal data structure for any article from any source. The `source_name` field tells you which newspaper it came from.

### The `SourceResult` Dataclass

```python
@dataclass
class SourceResult:
    source: NewsSource
    articles: list[Article] = field(default_factory=list)
    error: str = ""
```

A container for one source's results. If fetching fails, `error` contains the reason and `articles` is empty. This lets the emailer show a warning for that source instead of crashing.

The `field(default_factory=list)` is necessary because Python dataclasses can't use mutable defaults directly (all instances would share the same list object).

## Key Functions

### `_clean_html(raw_html: str) -> str`

RSS descriptions often contain embedded HTML. This function strips it down to clean text:

```python
text = re.sub(r"<img[^>]*>", "", raw_html)      # Remove images
text = re.sub(r"<br\s*/?>", "\n", text)          # Convert <br> to newlines
text = re.sub(r"<[^>]+>", "", text)              # Strip all remaining tags
text = html.unescape(text)                        # &amp; → &, &#8217; → '
text = re.sub(r"\n{3,}", "\n\n", text)           # Collapse excessive newlines
text = re.sub(r"[ \t]+", " ", text)              # Collapse whitespace runs
```

**Regex breakdown:**
- `r"<[^>]+>"` — matches any HTML tag. `<` is the literal bracket, `[^>]+` means "one or more characters that aren't `>`", and `>` is the closing bracket
- `r"<br\s*/?>"` — matches `<br>`, `<br/>`, and `<br />` variants. `\s*` handles optional whitespace, `/?` handles the optional slash

### `_fetch_single_source(source: NewsSource) -> SourceResult`

Fetches and parses the RSS feed for one source. This is where the actual HTTP request and XML parsing happen:

1. `requests.get(source.rss_url, timeout=30)` — fetch the feed
2. `response.raise_for_status()` — fail on HTTP errors (4xx/5xx)
3. `ET.fromstring(response.content)` — parse XML into a tree
4. `channel.findall("item")` — get all article elements
5. For each item (up to `source.max_articles`):
   - Extract title, link, pubDate
   - Try `<description>` first, then `<content:encoded>` (some feeds use this for richer content)
   - Clean the HTML, truncate to 300 characters if too long
   - Build an `Article` object
6. Return a `SourceResult` with the articles

**Critical design decision:** This function **never raises**. All exceptions are caught and stored in `SourceResult.error`:

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

This means if BBC's feed is down, you still get articles from ACM and NYTimes.

### `fetch_all_sources() -> list[SourceResult]`

The top-level function called by `main.py`. It:

1. Reads `SELECTED_SOURCES` from config (e.g., `["acm_technews", "bbc_tech"]`)
2. Resolves each key to a `NewsSource` via `get_source_by_key()`
3. Calls `_fetch_single_source()` for each
4. Prints progress as it goes (✔ for success, ⚠ for errors)
5. Returns the full list of `SourceResult` objects

## RSS Feed Specifics

All four sources use standard RSS 2.0 with the same core elements:

| Source | Feed URL | Max Articles | Notes |
|--------|----------|-------------|-------|
| ACM TechNews | `news.content.smithbucklin.com/acm/TechNews_rss.xml` | 10 | Mon/Wed/Fri only; hosted by Smithbucklin (ACM's management company) |
| MIT Technology Review | `www.technologyreview.com/feed/` | 5 | Daily updates |
| NYTimes Technology | `rss.nytimes.com/services/xml/rss/nyt/Technology.xml` | 5 | Daily updates |
| BBC News Technology | `feeds.bbci.co.uk/news/technology/rss.xml` | 5 | Frequent updates throughout the day |

### Why different `max_articles` limits?

ACM TechNews publishes its entire edition as one batch (~10 articles, 3 times per week). The other sources publish continuously — without a cap, you'd get 20+ articles from each, making the digest overwhelming. The limit keeps each source's section scannable.

## Content Handling Across Sources

Different feeds format descriptions differently:

- **ACM TechNews** — Rich HTML with images, anchor tags, and source attribution baked into the description
- **MIT Technology Review** — Short paragraph summaries, minimal HTML
- **NYTimes** — Clean plain-text descriptions
- **BBC** — Clean plain-text descriptions

The `_clean_html()` function handles all of these uniformly. The 300-character truncation prevents any source from dominating the digest with very long descriptions.

---

**Previous:** [04 — Config and Environment](04-config-and-environment.md)
**Next:** [06 — Emailer Deep Dive](06-emailer-deep-dive.md)
