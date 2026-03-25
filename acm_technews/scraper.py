# =============================================================================
# scraper.py — RSS Feed Scraper for ACM TechNews
# =============================================================================
#
# This module is responsible for one thing: reach out over the internet, grab
# the ACM TechNews RSS feed, and return structured Python objects that the
# rest of the application can work with.
#
# Why a separate scraper module?
# ------------------------------
# The "Single Responsibility Principle" — each file should have one reason to
# change.  If ACM changes its RSS format, only this file needs updating.  The
# emailer doesn't care how articles are fetched; it just receives a list.
#
# What is RSS?
# ------------
# RSS (Really Simple Syndication) is an XML-based format that websites use to
# publish lists of recent content.  Think of it as a machine-readable news
# feed.  Each <item> in the XML corresponds to one article with a title,
# description, and link.  We parse that XML with Python's built-in
# xml.etree.ElementTree — no extra dependency needed for XML parsing.
#
# Data flow:
#   Internet (HTTP GET) → raw XML bytes → ElementTree parse → list[Article]
#
# Key decisions:
#   - We use the `requests` library instead of urllib because it has a simpler
#     API, automatic encoding handling, and better error messages.
#   - We define an Article dataclass so consumers get named fields (a.title)
#     instead of opaque dictionary keys (a["title"]).
#   - The HTML-cleaning logic is gnarly because ACM's descriptions embed HTML
#     tags, images, and attribution lines inside the <description> CDATA.  We
#     strip all that down to plain text with regex.
#
# Dependencies:
#   requests — HTTP client library (installed via pip)
#   html, re, xml.etree.ElementTree, dataclasses — all stdlib
# =============================================================================

"""
Scraper module for ACM TechNews RSS feed.
"""

# html.unescape converts HTML entities like &amp; back to & and &lt; to <
import html

# re (regular expressions) lets us do pattern-based find-and-replace on
# strings.  We use it extensively to strip HTML tags from the RSS descriptions.
import re

# ElementTree is Python's built-in XML parser.  It reads XML into a tree of
# Element objects that we can walk with .find() and .findall().
import xml.etree.ElementTree as ET

# dataclass is a decorator that auto-generates __init__, __repr__, and
# __eq__ for a class based on its annotated fields.  It saves us from
# writing boilerplate constructor code.
from dataclasses import dataclass

# requests is the de-facto standard HTTP library for Python.  We use it to
# make a GET request to the RSS feed URL.
import requests

# Import the ACM TechNews URL constant from our central config module.
# (Currently unused here since we hard-code the RSS URL, but it's available
# if we ever need the main site URL.)
from acm_technews.config import ACM_TECHNEWS_URL

# The direct URL to the ACM TechNews RSS XML feed.  This is different from
# the human-readable technews.acm.org page — it returns raw XML that we can
# parse programmatically.
RSS_URL = "https://news.content.smithbucklin.com/acm/TechNews_rss.xml"

# How long (in seconds) we wait for the HTTP response before giving up.
# 30 seconds is generous; most responses come back in under 2 seconds.
# Without a timeout, a hung server could block the script forever.
REQUEST_TIMEOUT = 30


@dataclass
class Article:
    """
    Represents a single news article from the ACM TechNews digest.

    Fields:
        title  — headline of the article (e.g., "AI Helps Detect Cancer Earlier")
        blurb  — a short paragraph summarizing the article
        link   — URL to the full article on the original source's website
        source — attribution string like "The New York Times (03/24/26)"
    """
    title: str
    blurb: str
    link: str
    source: str


def _clean_html(raw_html: str) -> str:
    """
    Strip HTML tags and decode entities from a string.

    The RSS feed descriptions contain inline HTML (images, links, line breaks,
    spans).  We need to convert all of that to clean plain text so it can be
    used in both the plain-text email body and as a base for the HTML email.
    """
    # Remove <img> tags entirely — we don't need images in our digest
    text = re.sub(r"<img[^>]*>", "", raw_html)

    # Convert <br> / <br/> tags into actual newline characters
    text = re.sub(r"<br\s*/?>", "\n", text)

    # Remove anchor (<a>) tags and their text — we'll use our own links
    text = re.sub(r"<a[^>]*>.*?</a>", "", text)

    # Remove <span> tags and their contents (usually styling wrappers)
    text = re.sub(r"<span[^>]*>.*?</span>", "", text)

    # Catch-all: remove any remaining HTML tags we didn't handle above
    text = re.sub(r"<[^>]+>", "", text)

    # Decode HTML entities: &amp; → &, &#8217; → ', etc.
    text = html.unescape(text)

    # Collapse runs of 3+ newlines down to 2 (keeps it readable)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Strip leading/trailing whitespace and return
    return text.strip()


def _parse_description(desc_html: str) -> tuple[str, str]:
    """
    Extract the blurb and source line from an RSS item description.

    The raw description from the RSS feed looks roughly like this:

        SourceName<br/><br/>[img]Blurb text...<br/><br/>
        From "Article Title"<br/> SourceName (03/24/26) Author<br/>
        <a href="...">View Full Article</a>

    We split on the 'From "' marker to separate the blurb from the
    attribution block, then extract each piece.

    Returns:
        A tuple of (blurb_text, source_attribution_string).
    """
    # First, clean all HTML out so we're working with plain text
    # Then split on the 'From "' marker that precedes the attribution section
    from_match = re.split(r'\n\s*From\s+"', _clean_html(desc_html))

    if len(from_match) >= 2:
        # Everything before 'From "' is the blurb area
        blurb_raw = from_match[0]
        # Everything after is the source attribution area
        source_raw = from_match[1]
    else:
        # No 'From "' marker found — treat the whole thing as the blurb
        blurb_raw = _clean_html(desc_html)
        source_raw = ""

    # The first line of the blurb area is usually the source name (e.g.,
    # "The Wall Street Journal") — the actual blurb starts on line 2.
    blurb_lines = blurb_raw.strip().split("\n")
    if len(blurb_lines) > 1:
        # Grab the source name from the first line
        source_name = blurb_lines[0].strip()
        # Join the remaining lines as the actual blurb
        blurb = "\n".join(blurb_lines[1:]).strip()
    else:
        source_name = ""
        blurb = blurb_raw.strip()

    # Now try to find a clean source attribution with a date pattern like
    # (MM/DD/YY) inside the source_raw block.
    source_line = ""
    if source_raw:
        # source_raw looks like:  Article Title"\n SourceName (03/24/26) Author
        parts = source_raw.split("\n")
        for part in parts:
            # Strip quotes and whitespace from each line
            part = part.strip().strip('"')
            # Look for lines containing a date in (MM/DD/YY) format
            if part and re.search(r"\(\d{2}/\d{2}/\d{2}\)", part):
                source_line = part.strip()
                break  # Take the first match — that's our attribution line

    # Fall back to the source name we extracted from the blurb's first line
    if not source_line and source_name:
        source_line = source_name

    return blurb, source_line


def fetch_articles() -> tuple[str, list[Article]]:
    """
    Fetch and parse the ACM TechNews RSS feed.

    Makes an HTTP GET request to the RSS feed URL, parses the XML response,
    and converts each <item> element into an Article dataclass.

    Returns:
        A list of Article objects, one per news story in the feed.

    Raises:
        requests.HTTPError — if the server returns a 4xx/5xx status code
        requests.Timeout   — if the request exceeds REQUEST_TIMEOUT seconds
    """
    # Send an HTTP GET request to the RSS feed URL
    # timeout= prevents hanging forever if the server doesn't respond
    response = requests.get(RSS_URL, timeout=REQUEST_TIMEOUT)

    # Raise an exception for HTTP errors (404, 500, etc.)
    # Without this, a 500 response would silently proceed with garbage data
    response.raise_for_status()

    # Parse the raw XML bytes into an ElementTree structure
    root = ET.fromstring(response.content)

    # RSS feeds have a <channel> element that contains all the <item> elements
    channel = root.find("channel")

    # Build our list of Article objects
    articles = []
    for item in channel.findall("item"):
        # Extract text content from each child element, defaulting to ""
        title = item.findtext("title", "").strip()
        link = item.findtext("link", "").strip()
        desc_html = item.findtext("description", "")

        # Parse the messy HTML description into a clean blurb and source
        blurb, source = _parse_description(desc_html)

        # Construct an Article dataclass and add it to our list
        articles.append(Article(
            title=title,
            blurb=blurb,
            link=link,
            source=source,
        ))

    return articles


# ---------------------------------------------------------------------------
# Standalone test harness
# ---------------------------------------------------------------------------
# When you run `python scraper.py` directly (instead of importing it), this
# block executes.  It's a quick way to verify the scraper works without
# sending any email.
if __name__ == "__main__":
    arts = fetch_articles()
    for a in arts:
        print(f"TITLE: {a.title}")
        print(f"BLURB: {a.blurb[:120]}...")
        print(f"LINK:  {a.link}")
        print(f"SRC:   {a.source}")
        print("---")
