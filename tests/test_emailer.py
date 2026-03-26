"""
Tests for newsdigest.emailer — email formatting and sending.

SMTP calls are mocked so no real emails are sent.
"""

from unittest.mock import patch, MagicMock
from datetime import datetime

from newsdigest.scraper import Article, SourceResult
from newsdigest.sources import NewsSource
from newsdigest.emailer import (
    _time_greeting,
    _edition_date,
    build_plain_text,
    build_html,
    send_email,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_results(n_articles: int = 2, include_error: bool = False) -> list[SourceResult]:
    """Build a results list for email tests."""
    source = NewsSource(
        key="test", name="Test News", description="d",
        rss_url="https://example.com/rss", max_articles=5,
    )
    articles = [
        Article(
            title=f"Article {i+1}",
            description=f"Description {i+1}",
            link=f"https://example.com/{i+1}",
            source_name="Test News",
        )
        for i in range(n_articles)
    ]
    results = [SourceResult(source=source, articles=articles)]

    if include_error:
        error_source = NewsSource(
            key="err", name="Broken Source", description="d",
            rss_url="https://broken.com/rss", max_articles=5,
        )
        results.append(SourceResult(source=error_source, error="Connection failed"))

    return results


# ---------------------------------------------------------------------------
# _time_greeting
# ---------------------------------------------------------------------------

class TestTimeGreeting:

    @patch("newsdigest.emailer.datetime")
    def test_morning(self, mock_dt):
        mock_dt.now.return_value = datetime(2026, 1, 1, 8, 0)
        assert _time_greeting() == "Good morning"

    @patch("newsdigest.emailer.datetime")
    def test_afternoon(self, mock_dt):
        mock_dt.now.return_value = datetime(2026, 1, 1, 14, 0)
        assert _time_greeting() == "Good afternoon"

    @patch("newsdigest.emailer.datetime")
    def test_evening(self, mock_dt):
        mock_dt.now.return_value = datetime(2026, 1, 1, 20, 0)
        assert _time_greeting() == "Good evening"

    @patch("newsdigest.emailer.datetime")
    def test_midnight_is_morning(self, mock_dt):
        mock_dt.now.return_value = datetime(2026, 1, 1, 0, 0)
        assert _time_greeting() == "Good morning"

    @patch("newsdigest.emailer.datetime")
    def test_noon_is_afternoon(self, mock_dt):
        mock_dt.now.return_value = datetime(2026, 1, 1, 12, 0)
        assert _time_greeting() == "Good afternoon"

    @patch("newsdigest.emailer.datetime")
    def test_5pm_is_evening(self, mock_dt):
        mock_dt.now.return_value = datetime(2026, 1, 1, 17, 0)
        assert _time_greeting() == "Good evening"


# ---------------------------------------------------------------------------
# _edition_date
# ---------------------------------------------------------------------------

class TestEditionDate:

    def test_format(self):
        result = _edition_date()
        # Should match the format "Month DD, YYYY"
        from datetime import datetime as dt
        expected = dt.now().strftime("%B %d, %Y")
        assert result == expected


# ---------------------------------------------------------------------------
# build_plain_text
# ---------------------------------------------------------------------------

class TestBuildPlainText:

    def test_contains_greeting(self):
        text = build_plain_text(_make_results())
        assert "Good" in text  # morning/afternoon/evening

    def test_contains_article_titles(self):
        text = build_plain_text(_make_results())
        assert "Article 1" in text
        assert "Article 2" in text

    def test_contains_article_links(self):
        text = build_plain_text(_make_results())
        assert "https://example.com/1" in text

    def test_contains_source_name(self):
        text = build_plain_text(_make_results())
        assert "Test News" in text

    def test_error_source_shows_warning(self):
        text = build_plain_text(_make_results(include_error=True))
        assert "Broken Source" in text
        assert "Connection failed" in text

    def test_empty_results_no_crash(self):
        text = build_plain_text([])
        assert isinstance(text, str)

    def test_footer_present(self):
        text = build_plain_text(_make_results())
        assert "News Digest bot" in text


# ---------------------------------------------------------------------------
# build_html
# ---------------------------------------------------------------------------

class TestBuildHtml:

    def test_returns_valid_html(self):
        html = build_html(_make_results())
        assert html.startswith("<!DOCTYPE html>")
        assert "</html>" in html

    def test_contains_article_titles(self):
        html = build_html(_make_results())
        assert "Article 1" in html
        assert "Article 2" in html

    def test_contains_links(self):
        html = build_html(_make_results())
        assert 'href="https://example.com/1"' in html

    def test_error_source_styled(self):
        html = build_html(_make_results(include_error=True))
        assert "Broken Source" in html
        assert "Connection failed" in html

    def test_empty_results_no_crash(self):
        html = build_html([])
        assert "<!DOCTYPE html>" in html

    def test_escapes_untrusted_feed_content(self):
        source = NewsSource(
            key="test", name='Bad <Source>', description="d",
            rss_url="https://example.com/rss", max_articles=5,
        )
        article = Article(
            title='<script>alert("x")</script>',
            description='Hello <b>world</b>',
            link='javascript:alert("x")',
            source_name="Bad Source",
        )
        html = build_html([SourceResult(source=source, articles=[article])])

        assert '<script>alert("x")</script>' not in html
        assert "&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;" in html
        assert "Hello &lt;b&gt;world&lt;/b&gt;" in html
        assert 'href="javascript:alert(' not in html
        assert "Link unavailable" in html


# ---------------------------------------------------------------------------
# send_email (mocked SMTP)
# ---------------------------------------------------------------------------

class TestSendEmail:

    @patch("newsdigest.emailer.SMTP_EMAIL", "test@gmail.com")
    @patch("newsdigest.emailer.SMTP_APP_PASSWORD", "fakepassword")
    @patch("newsdigest.emailer.RECIPIENT_EMAIL", "recipient@gmail.com")
    @patch("newsdigest.emailer.smtplib.SMTP")
    def test_sends_via_smtp(self, mock_smtp_class):
        mock_server = MagicMock()
        mock_smtp_class.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_class.return_value.__exit__ = MagicMock(return_value=False)

        send_email(_make_results())

        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("test@gmail.com", "fakepassword")
        mock_server.sendmail.assert_called_once()
        args = mock_server.sendmail.call_args[0]
        assert args[0] == "test@gmail.com"
        assert args[1] == "recipient@gmail.com"

    @patch("newsdigest.emailer.SMTP_EMAIL", "test@gmail.com")
    @patch("newsdigest.emailer.SMTP_APP_PASSWORD", "fakepassword")
    @patch("newsdigest.emailer.RECIPIENT_EMAIL", "recipient@gmail.com")
    @patch("newsdigest.emailer.smtplib.SMTP")
    def test_email_contains_multipart(self, mock_smtp_class):
        mock_server = MagicMock()
        mock_smtp_class.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_class.return_value.__exit__ = MagicMock(return_value=False)

        send_email(_make_results())

        raw_msg = mock_server.sendmail.call_args[0][2]
        assert "multipart/alternative" in raw_msg
        assert "text/plain" in raw_msg
        assert "text/html" in raw_msg


# ---------------------------------------------------------------------------
# No new articles today rendering
# ---------------------------------------------------------------------------

class TestNoNewToday:

    def _make_stale_result(self) -> list[SourceResult]:
        source = NewsSource(
            key="acm", name="ACM TechNews", description="d",
            rss_url="https://example.com/rss", max_articles=5,
        )
        return [SourceResult(source=source, articles=[], no_new_today=True)]

    def test_plain_text_shows_no_new_message(self):
        text = build_plain_text(self._make_stale_result())
        assert "ACM TechNews" in text
        assert "No new articles published today" in text

    def test_html_shows_no_new_message(self):
        result = build_html(self._make_stale_result())
        assert "ACM TechNews" in result
        assert "No new articles published today" in result

    def test_plain_text_mixed_fresh_and_stale(self):
        fresh_source = NewsSource(
            key="bbc", name="BBC News", description="d",
            rss_url="https://example.com/rss", max_articles=5,
        )
        stale_source = NewsSource(
            key="acm", name="ACM TechNews", description="d",
            rss_url="https://example.com/rss", max_articles=5,
        )
        article = Article(
            title="Fresh Article", description="desc",
            link="https://example.com/1", source_name="BBC News",
        )
        results = [
            SourceResult(source=fresh_source, articles=[article]),
            SourceResult(source=stale_source, articles=[], no_new_today=True),
        ]
        text = build_plain_text(results)
        assert "Fresh Article" in text
        assert "BBC News" in text
        assert "ACM TechNews" in text
        assert "No new articles published today" in text

    def test_html_mixed_fresh_and_stale(self):
        fresh_source = NewsSource(
            key="bbc", name="BBC News", description="d",
            rss_url="https://example.com/rss", max_articles=5,
        )
        stale_source = NewsSource(
            key="acm", name="ACM TechNews", description="d",
            rss_url="https://example.com/rss", max_articles=5,
        )
        article = Article(
            title="Fresh Article", description="desc",
            link="https://example.com/1", source_name="BBC News",
        )
        results = [
            SourceResult(source=fresh_source, articles=[article]),
            SourceResult(source=stale_source, articles=[], no_new_today=True),
        ]
        result = build_html(results)
        assert "Fresh Article" in result
        assert "ACM TechNews" in result
        assert "No new articles published today" in result
