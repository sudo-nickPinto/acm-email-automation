# =============================================================================
# scraper.py — Multi-Source RSS Feed Scraper (v2)
# =============================================================================
#
# This module fetches articles from one or more RSS feeds and returns them
# as structured Article objects grouped by source.
#
# What changed from v1:
# ---------------------
# v1 only knew about ACM TechNews and had ACM-specific HTML parsing baked in.
# v2 fetches from any standard RSS 2.0 feed.  Each source in sources.py has
# its own RSS URL, and the scraper handles them all uniformly.
#
# Data flow:
#   config.SELECTED_SOURCES → resolve to NewsSource objects → HTTP GET each
#   RSS URL → parse XML → list[Article] per source → dict of all results
#
# Dependencies:
#   requests — HTTP client (pip install)
#   html, re, xml.etree.ElementTree, dataclasses — all stdlib
# =============================================================================

"""
Multi-source RSS feed scraper.  Fetches and parses articles from
all sources the user selected during setup.
"""

import html
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import date
from email.utils import parsedate_to_datetime

import requests

from newsdigest.config import SELECTED_SOURCES
from newsdigest.sources import AVAILABLE_SOURCES, NewsSource, get_source_by_key


# How long (in seconds) to wait for each HTTP response before giving up.
REQUEST_TIMEOUT: int = 30


@dataclass
class Article:
    """
    Represents a single news article from any source.

    Fields:
        title       — Headline of the article
        description — Short summary or blurb
        link        — URL to the full article
        source_name — Human-readable name of the newspaper it came from
        pub_date    — Publication date string from the RSS feed (optional)
    """
    title: str
    description: str
    link: str
    source_name: str
    pub_date: str = ""


@dataclass
class SourceResult:
    """
    Container for all articles fetched from a single source.

    Fields:
        source   — The NewsSource metadata (name, key, URL, etc.)
        articles — List of Article objects parsed from the feed
        error    — Error message if fetching failed, empty string if OK
    """
    source: NewsSource
    articles: list[Article] = field(default_factory=list)
    error: str = ""
    no_new_today: bool = False


def _parse_pub_date(pub_date_str: str) -> date | None:
    """
    Parse an RSS pubDate string (RFC 822) into a local date.

    Converts to the user's local timezone before extracting the date,
    so "today" comparisons match what the user expects.

    Returns None if the string is empty or unparseable.
    """
    if not pub_date_str:
        return None
    try:
        dt = parsedate_to_datetime(pub_date_str)
        return dt.astimezone().date()
    except (ValueError, TypeError):
        return None


def _is_published_today(pub_date_str: str) -> bool:
    """
    Check if an article's pubDate falls on today's date (local time).
    """
    pub = _parse_pub_date(pub_date_str)
    if pub is None:
        return False
    return pub == date.today()


def _clean_html(raw_html: str) -> str:
    """
    Strip HTML tags and decode entities from a string.

    RSS feed descriptions often contain embedded HTML (images, links,
    line breaks, formatting tags).  We need clean plain text.
    """
    # Remove <img> tags entirely
    text = re.sub(r"<img[^>]*>", "", raw_html)

    # Convert <br> / <br/> to newlines
    text = re.sub(r"<br\s*/?>", "\n", text)

    # Remove all remaining HTML tags
    text = re.sub(r"<[^>]+>", "", text)

    # Decode HTML entities: &amp; → &, &#8217; → ', etc.
    text = html.unescape(text)

    # Collapse excessive whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)

    return text.strip()


def _fetch_single_source(source: NewsSource) -> SourceResult:
    """
    Fetch and parse the RSS feed for a single source.

    Makes an HTTP GET request, parses the XML, and extracts articles
    up to the source's max_articles limit.

    Returns a SourceResult — either with articles or an error message.
    Never raises; errors are captured in the result.
    """
    try:
        # Fetch the RSS feed
        response = requests.get(source.rss_url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        # Parse XML
        root = ET.fromstring(response.content)
        channel = root.find("channel")

        if channel is None:
            return SourceResult(source=source, error="No <channel> element in feed")

        # Extract articles from <item> elements
        articles: list[Article] = []
        items = channel.findall("item")

        for item in items[:source.max_articles]:
            title = item.findtext("title", "").strip()
            link = item.findtext("link", "").strip()
            pub_date = item.findtext("pubDate", "").strip()

            # Description could be in <description> or <content:encoded>
            # Try description first, fall back to content:encoded
            desc_raw = item.findtext("description", "")

            # Some feeds put richer content in content:encoded
            # (namespace: http://purl.org/rss/1.0/modules/content/)
            content_ns = "{http://purl.org/rss/1.0/modules/content/}"
            content_encoded = item.findtext(f"{content_ns}encoded", "")

            # Use description for the blurb (shorter), fall back to encoded
            if desc_raw.strip():
                description = _clean_html(desc_raw)
            elif content_encoded.strip():
                description = _clean_html(content_encoded)
            else:
                description = ""

            # Truncate very long descriptions to keep the digest scannable
            if len(description) > 300:
                description = description[:297] + "..."

            if title:  # Skip items with no title
                articles.append(Article(
                    title=title,
                    description=description,
                    link=link,
                    source_name=source.name,
                    pub_date=pub_date,
                ))

        return SourceResult(source=source, articles=articles)

    except requests.Timeout:
        return SourceResult(source=source, error=f"Timed out after {REQUEST_TIMEOUT}s")
    except requests.HTTPError as e:
        return SourceResult(source=source, error=f"HTTP error: {e.response.status_code}")
    except requests.ConnectionError:
        return SourceResult(source=source, error="Connection failed — check your internet")
    except ET.ParseError:
        return SourceResult(source=source, error="Failed to parse XML from feed")


def fetch_all_sources() -> list[SourceResult]:
    """
    Fetch articles from all sources the user selected during setup.

    Reads SELECTED_SOURCES from config, resolves each key to a NewsSource,
    fetches each feed, and returns a list of SourceResult objects.

    Sources that fail are included in the results with an error message
    rather than crashing the whole run.
    """
    results: list[SourceResult] = []

    for key in SELECTED_SOURCES:
        source = get_source_by_key(key)
        if source is None:
            print(f"  Warning: Unknown source key '{key}' in config — skipping")
            continue

        print(f"  Fetching {source.name}...")
        result = _fetch_single_source(source)

        if result.error:
            print(f"  ⚠ {source.name}: {result.error}")
        else:
            print(f"  ✔ {source.name}: {len(result.articles)} articles")

        results.append(result)

    return results


def fetch_single_source_by_key(key: str) -> SourceResult | None:
    """
    Fetch articles from a single source by its key.
    Useful for testing individual sources.
    """
    source = get_source_by_key(key)
    if source is None:
        return None
    return _fetch_single_source(source)


# ---------------------------------------------------------------------------
# Standalone test harness
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("Testing all available sources...\n")
    for source in AVAILABLE_SOURCES:
        print(f"--- {source.name} ---")
        result = _fetch_single_source(source)
        if result.error:
            print(f"  ERROR: {result.error}")
        else:
            for a in result.articles[:3]:
                print(f"  TITLE: {a.title}")
                print(f"  DESC:  {a.description[:100]}...")
                print(f"  LINK:  {a.link}")
                print()
        print()
