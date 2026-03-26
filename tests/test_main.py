"""
Tests for main.py — orchestrator logic (hashing, dedup, CLI flags).

All network and email sending is mocked.
"""

import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock

from newsdigest.scraper import Article, SourceResult
from newsdigest.sources import NewsSource

from main import _results_hash, _already_sent, _save_state, main, STATE_FILE


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_results(titles: list[str] | None = None) -> list[SourceResult]:
    if titles is None:
        titles = ["Title A", "Title B"]
    source = NewsSource(
        key="t", name="T", description="d",
        rss_url="https://x.com/rss", max_articles=5,
    )
    articles = [
        Article(title=t, description="d", link="https://x.com", source_name="T")
        for t in titles
    ]
    return [SourceResult(source=source, articles=articles)]


# ---------------------------------------------------------------------------
# _results_hash
# ---------------------------------------------------------------------------

class TestResultsHash:

    def test_deterministic(self):
        r = _make_results(["A", "B"])
        assert _results_hash(r) == _results_hash(r)

    def test_different_titles_different_hash(self):
        r1 = _make_results(["A"])
        r2 = _make_results(["B"])
        assert _results_hash(r1) != _results_hash(r2)

    def test_returns_sha256_hex(self):
        h = _results_hash(_make_results())
        assert len(h) == 64  # SHA-256 hex digest length

    def test_empty_results(self):
        h = _results_hash([])
        assert len(h) == 64


# ---------------------------------------------------------------------------
# _already_sent / _save_state
# ---------------------------------------------------------------------------

class TestStateTracking:

    def test_not_sent_when_no_file(self, tmp_path):
        fake_state = tmp_path / ".last_sent"
        with patch("main.STATE_FILE", fake_state):
            assert _already_sent("abc123") is False

    def test_sent_when_hash_matches(self, tmp_path):
        fake_state = tmp_path / ".last_sent"
        fake_state.write_text("abc123")
        with patch("main.STATE_FILE", fake_state):
            assert _already_sent("abc123") is True

    def test_not_sent_when_hash_differs(self, tmp_path):
        fake_state = tmp_path / ".last_sent"
        fake_state.write_text("old_hash")
        with patch("main.STATE_FILE", fake_state):
            assert _already_sent("new_hash") is False

    def test_save_state_writes(self, tmp_path):
        fake_state = tmp_path / ".last_sent"
        with patch("main.STATE_FILE", fake_state):
            _save_state("myhash")
        assert fake_state.read_text() == "myhash"


# ---------------------------------------------------------------------------
# main() — integration-level tests with mocked I/O
# ---------------------------------------------------------------------------

class TestMain:

    @patch("main.SELECTED_SOURCES", [])
    def test_exits_when_no_sources(self):
        import pytest
        with pytest.raises(SystemExit):
            main()

    @patch("main._save_state")
    @patch("main.send_email")
    @patch("main.fetch_all_sources")
    @patch("main._already_sent", return_value=False)
    @patch("main.SELECTED_SOURCES", ["bbc_tech"])
    def test_sends_email_on_new_content(
        self, mock_already, mock_fetch, mock_send, mock_save
    ):
        mock_fetch.return_value = _make_results()
        with patch("sys.argv", ["main.py"]):
            main()
        mock_send.assert_called_once()
        mock_save.assert_called_once()

    @patch("main.send_email")
    @patch("main.fetch_all_sources")
    @patch("main._already_sent", return_value=True)
    @patch("main.SELECTED_SOURCES", ["bbc_tech"])
    def test_skips_when_already_sent(self, mock_already, mock_fetch, mock_send):
        mock_fetch.return_value = _make_results()
        import pytest
        with patch("sys.argv", ["main.py"]):
            with pytest.raises(SystemExit):
                main()
        mock_send.assert_not_called()

    @patch("main._save_state")
    @patch("main.send_email")
    @patch("main.fetch_all_sources")
    @patch("main._already_sent", return_value=True)
    @patch("main.SELECTED_SOURCES", ["bbc_tech"])
    def test_force_flag_overrides_dedup(
        self, mock_already, mock_fetch, mock_send, mock_save
    ):
        mock_fetch.return_value = _make_results()
        with patch("sys.argv", ["main.py", "--force"]):
            main()
        mock_send.assert_called_once()

    @patch("main.build_plain_text", return_value="preview text")
    @patch("main.send_email")
    @patch("main.fetch_all_sources")
    @patch("main._already_sent", return_value=False)
    @patch("main.SELECTED_SOURCES", ["bbc_tech"])
    def test_dry_run_does_not_send(
        self, mock_already, mock_fetch, mock_send, mock_build
    ):
        mock_fetch.return_value = _make_results()
        with patch("sys.argv", ["main.py", "--dry-run"]):
            main()
        mock_send.assert_not_called()

    @patch("main.send_email")
    @patch("main.fetch_all_sources")
    @patch("main.SELECTED_SOURCES", ["bbc_tech"])
    def test_exits_when_no_articles(self, mock_fetch, mock_send):
        source = NewsSource(
            key="t", name="T", description="d",
            rss_url="https://x.com/rss", max_articles=5,
        )
        mock_fetch.return_value = [SourceResult(source=source, articles=[])]
        import pytest
        with patch("sys.argv", ["main.py"]):
            with pytest.raises(SystemExit):
                main()
        mock_send.assert_not_called()

    @patch("main._save_state")
    @patch("main.send_email")
    @patch("main.fetch_all_sources")
    @patch("main._already_sent", return_value=False)
    @patch("main.SELECTED_SOURCES", ["acm_technews", "bbc_tech"])
    def test_stale_source_still_sends(
        self, mock_already, mock_fetch, mock_send, mock_save
    ):
        """When one source has no new articles today, email still sends."""
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        today_rfc822 = now.strftime("%a, %d %b %Y %H:%M:%S +0000")

        fresh_source = NewsSource(
            key="bbc", name="BBC", description="d",
            rss_url="https://x.com/rss", max_articles=5,
        )
        stale_source = NewsSource(
            key="acm", name="ACM", description="d",
            rss_url="https://x.com/rss", max_articles=5,
        )
        fresh_article = Article(
            title="Today", description="d",
            link="https://x.com", source_name="BBC",
            pub_date=today_rfc822,
        )
        old_article = Article(
            title="Old", description="d",
            link="https://x.com", source_name="ACM",
            pub_date="Mon, 01 Jan 2024 08:00:00 GMT",
        )
        mock_fetch.return_value = [
            SourceResult(source=fresh_source, articles=[fresh_article]),
            SourceResult(source=stale_source, articles=[old_article]),
        ]
        with patch("sys.argv", ["main.py"]):
            main()
        mock_send.assert_called_once()
        # Verify the stale source got flagged
        sent_results = mock_send.call_args[0][0]
        stale_results = [r for r in sent_results if r.no_new_today]
        assert len(stale_results) == 1
        assert stale_results[0].source.key == "acm"

    @patch("main._save_state")
    @patch("main.send_email")
    @patch("main.fetch_all_sources")
    @patch("main._already_sent", return_value=False)
    @patch("main.SELECTED_SOURCES", ["acm_technews"])
    def test_all_stale_still_sends(
        self, mock_already, mock_fetch, mock_send, mock_save
    ):
        """When ALL sources are stale (no articles today), email still sends."""
        stale_source = NewsSource(
            key="acm", name="ACM", description="d",
            rss_url="https://x.com/rss", max_articles=5,
        )
        old_article = Article(
            title="Old", description="d",
            link="https://x.com", source_name="ACM",
            pub_date="Mon, 01 Jan 2024 08:00:00 GMT",
        )
        mock_fetch.return_value = [
            SourceResult(source=stale_source, articles=[old_article]),
        ]
        with patch("sys.argv", ["main.py"]):
            main()
        mock_send.assert_called_once()
