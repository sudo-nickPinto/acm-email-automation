"""
Shared fixtures and helpers for the News Digest test suite.
"""

import pytest
from newsdigest.sources import NewsSource
from newsdigest.scraper import Article, SourceResult


# ---------------------------------------------------------------------------
# Reusable factory fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_source() -> NewsSource:
    """A minimal NewsSource for tests that don't hit the network."""
    return NewsSource(
        key="test_source",
        name="Test News",
        description="A fake source for testing",
        rss_url="https://example.com/rss.xml",
        max_articles=3,
    )


@pytest.fixture
def sample_article() -> Article:
    """A single Article for unit tests."""
    return Article(
        title="Test Article Title",
        description="This is a test description.",
        link="https://example.com/article/1",
        source_name="Test News",
        pub_date="Mon, 01 Jan 2026 08:00:00 GMT",
    )


@pytest.fixture
def sample_results(sample_source, sample_article) -> list[SourceResult]:
    """A list with one successful SourceResult containing one article."""
    return [
        SourceResult(
            source=sample_source,
            articles=[sample_article],
        )
    ]


@pytest.fixture
def error_result(sample_source) -> SourceResult:
    """A SourceResult that represents a failed fetch."""
    return SourceResult(
        source=sample_source,
        error="Connection failed — check your internet",
    )


@pytest.fixture
def empty_result(sample_source) -> SourceResult:
    """A SourceResult with no articles and no error."""
    return SourceResult(source=sample_source, articles=[])


# ---------------------------------------------------------------------------
# Sample RSS XML for scraper tests
# ---------------------------------------------------------------------------

SAMPLE_RSS_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Test Feed</title>
    <item>
      <title>First Article</title>
      <description>Description of the first article.</description>
      <link>https://example.com/1</link>
      <pubDate>Mon, 01 Jan 2026 08:00:00 GMT</pubDate>
    </item>
    <item>
      <title>Second Article</title>
      <description>&lt;p&gt;HTML &amp; entities&lt;/p&gt;</description>
      <link>https://example.com/2</link>
      <pubDate>Tue, 02 Jan 2026 08:00:00 GMT</pubDate>
    </item>
    <item>
      <title>Third Article</title>
      <description>Third description.</description>
      <link>https://example.com/3</link>
    </item>
    <item>
      <title>Fourth Article</title>
      <description>Fourth — over the limit.</description>
      <link>https://example.com/4</link>
    </item>
  </channel>
</rss>
"""

SAMPLE_RSS_NO_CHANNEL = """\
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
</rss>
"""

SAMPLE_RSS_EMPTY_ITEMS = """\
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Empty Feed</title>
  </channel>
</rss>
"""
