"""
Tests for newsdigest.scraper — RSS fetching, XML parsing, HTML cleaning.

All network calls are mocked so tests run offline and fast.
"""

from unittest.mock import patch, MagicMock
import xml.etree.ElementTree as ET

import requests

from newsdigest.sources import NewsSource
from newsdigest.scraper import (
    Article,
    SourceResult,
    _clean_html,
    _fetch_single_source,
    fetch_all_sources,
    fetch_single_source_by_key,
    REQUEST_TIMEOUT,
)
from tests.conftest import SAMPLE_RSS_XML, SAMPLE_RSS_NO_CHANNEL, SAMPLE_RSS_EMPTY_ITEMS


# ---------------------------------------------------------------------------
# _clean_html
# ---------------------------------------------------------------------------

class TestCleanHtml:

    def test_strips_tags(self):
        assert _clean_html("<p>Hello <b>World</b></p>") == "Hello World"

    def test_removes_img_tags(self):
        result = _clean_html('<img src="x.jpg" alt="pic"> text')
        assert "img" not in result
        assert "text" in result

    def test_converts_br_to_newline(self):
        result = _clean_html("line1<br>line2<br/>line3")
        assert "line1\nline2\nline3" == result

    def test_decodes_entities(self):
        assert _clean_html("&amp; &lt; &gt;") == "& < >"

    def test_collapses_whitespace(self):
        result = _clean_html("a     b")
        assert result == "a b"

    def test_empty_string(self):
        assert _clean_html("") == ""

    def test_plain_text_unchanged(self):
        assert _clean_html("no html here") == "no html here"


# ---------------------------------------------------------------------------
# _fetch_single_source (mocked network)
# ---------------------------------------------------------------------------

class TestFetchSingleSource:

    def _make_source(self, max_articles: int = 3) -> NewsSource:
        return NewsSource(
            key="test", name="Test", description="d",
            rss_url="https://example.com/rss.xml", max_articles=max_articles,
        )

    @patch("newsdigest.scraper.requests.get")
    def test_success_parses_articles(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.content = SAMPLE_RSS_XML.encode()
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        source = self._make_source(max_articles=3)
        result = _fetch_single_source(source)

        assert result.error == ""
        assert len(result.articles) == 3  # max_articles caps at 3
        assert result.articles[0].title == "First Article"
        assert result.articles[0].source_name == "Test"

    @patch("newsdigest.scraper.requests.get")
    def test_max_articles_limit(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.content = SAMPLE_RSS_XML.encode()
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        source = self._make_source(max_articles=2)
        result = _fetch_single_source(source)
        assert len(result.articles) == 2

    @patch("newsdigest.scraper.requests.get")
    def test_no_channel_returns_error(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.content = SAMPLE_RSS_NO_CHANNEL.encode()
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        result = _fetch_single_source(self._make_source())
        assert "No <channel>" in result.error

    @patch("newsdigest.scraper.requests.get")
    def test_empty_feed_returns_no_articles(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.content = SAMPLE_RSS_EMPTY_ITEMS.encode()
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        result = _fetch_single_source(self._make_source())
        assert result.error == ""
        assert len(result.articles) == 0

    @patch("newsdigest.scraper.requests.get")
    def test_timeout_returns_error(self, mock_get):
        mock_get.side_effect = requests.Timeout()
        result = _fetch_single_source(self._make_source())
        assert "Timed out" in result.error

    @patch("newsdigest.scraper.requests.get")
    def test_http_error_returns_error(self, mock_get):
        resp = MagicMock()
        resp.status_code = 404
        mock_get.side_effect = requests.HTTPError(response=resp)
        result = _fetch_single_source(self._make_source())
        assert "HTTP error" in result.error

    @patch("newsdigest.scraper.requests.get")
    def test_connection_error_returns_error(self, mock_get):
        mock_get.side_effect = requests.ConnectionError()
        result = _fetch_single_source(self._make_source())
        assert "Connection failed" in result.error

    @patch("newsdigest.scraper.requests.get")
    def test_invalid_xml_returns_error(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.content = b"not xml at all"
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        result = _fetch_single_source(self._make_source())
        assert "parse XML" in result.error

    @patch("newsdigest.scraper.requests.get")
    def test_html_in_description_is_cleaned(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.content = SAMPLE_RSS_XML.encode()
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        result = _fetch_single_source(self._make_source())
        second = result.articles[1]
        # The second article has <p>HTML &amp; entities</p> in desc
        assert "<p>" not in second.description
        assert "HTML & entities" in second.description

    @patch("newsdigest.scraper.requests.get")
    def test_long_description_truncated(self, mock_get):
        long_desc = "A" * 500
        xml = f"""<?xml version="1.0"?>
        <rss><channel><item>
            <title>Long</title>
            <description>{long_desc}</description>
            <link>https://x.com</link>
        </item></channel></rss>"""
        mock_resp = MagicMock()
        mock_resp.content = xml.encode()
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        result = _fetch_single_source(self._make_source())
        assert len(result.articles[0].description) <= 300


# ---------------------------------------------------------------------------
# fetch_all_sources (mocked config + network)
# ---------------------------------------------------------------------------

class TestFetchAllSources:

    @patch("newsdigest.scraper.requests.get")
    @patch("newsdigest.scraper.SELECTED_SOURCES", ["bbc_tech"])
    def test_fetches_selected_sources(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.content = SAMPLE_RSS_XML.encode()
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        results = fetch_all_sources()
        assert len(results) == 1
        assert results[0].source.key == "bbc_tech"

    @patch("newsdigest.scraper.SELECTED_SOURCES", ["nonexistent_key"])
    def test_skips_unknown_keys(self):
        results = fetch_all_sources()
        assert len(results) == 0


# ---------------------------------------------------------------------------
# fetch_single_source_by_key
# ---------------------------------------------------------------------------

class TestFetchSingleSourceByKey:

    def test_returns_none_for_unknown_key(self):
        result = fetch_single_source_by_key("does_not_exist")
        assert result is None

    @patch("newsdigest.scraper.requests.get")
    def test_returns_result_for_valid_key(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.content = SAMPLE_RSS_XML.encode()
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        result = fetch_single_source_by_key("bbc_tech")
        assert result is not None
        assert len(result.articles) > 0


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

class TestConstants:

    def test_request_timeout_positive(self):
        assert REQUEST_TIMEOUT > 0
