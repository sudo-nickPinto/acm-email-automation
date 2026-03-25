# =============================================================================
# sources.py — Registry of Available Newspaper RSS Feeds
# =============================================================================
#
# This module defines every newspaper source that users can subscribe to.
# Each source has a human-readable name, a short description (shown during
# setup), and an RSS feed URL.
#
# Why a dataclass?
# ----------------
# A dict like {"name": "BBC", "url": "..."} works but gives you no IDE
# autocompletion, no typo protection, and no documentation.  A dataclass
# gives you named fields (source.name), a readable __repr__, and a single
# place to see what a "source" is.
#
# Adding a new source:
# --------------------
# 1. Create a new NewsSource(...) instance
# 2. Add it to the AVAILABLE_SOURCES list
# 3. That's it — the wizard, scraper, and emailer all pick it up automatically
#
# Dependencies: None (stdlib only)
# =============================================================================

"""
Registry of newspaper RSS feed sources available for the digest.
"""

from dataclasses import dataclass


@dataclass
class NewsSource:
    """
    Represents a single newspaper/news source that can be included in the digest.

    Fields:
        key         — Short unique identifier, stored in .env (e.g., "bbc_tech")
        name        — Human-readable display name (e.g., "BBC News — Technology")
        description — One-line description shown during setup wizard
        rss_url     — URL to the source's RSS/XML feed
        max_articles — Maximum number of articles to include from this source
    """
    key: str
    name: str
    description: str
    rss_url: str
    max_articles: int = 5


# =============================================================================
# Available sources — add new newspapers here
# =============================================================================
# Each source appears as a numbered option in the setup wizard.
# The user picks which ones they want, and only those get fetched + emailed.
# =============================================================================

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


def get_source_by_key(key: str) -> NewsSource | None:
    """
    Look up a source by its unique key string.

    Returns the matching NewsSource, or None if no match.
    Used by the scraper to resolve the user's saved selections.
    """
    for source in AVAILABLE_SOURCES:
        if source.key == key:
            return source
    return None
