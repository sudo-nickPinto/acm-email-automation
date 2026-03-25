"""
Tests for newsdigest.sources — source registry and lookup.
"""

from newsdigest.sources import AVAILABLE_SOURCES, NewsSource, get_source_by_key


# ---------------------------------------------------------------------------
# AVAILABLE_SOURCES validation
# ---------------------------------------------------------------------------

class TestAvailableSources:
    """Verify the global source registry is well-formed."""

    def test_sources_not_empty(self):
        assert len(AVAILABLE_SOURCES) > 0

    def test_all_sources_are_newsource(self):
        for src in AVAILABLE_SOURCES:
            assert isinstance(src, NewsSource)

    def test_keys_are_unique(self):
        keys = [s.key for s in AVAILABLE_SOURCES]
        assert len(keys) == len(set(keys)), "Duplicate keys found"

    def test_every_source_has_rss_url(self):
        for src in AVAILABLE_SOURCES:
            assert src.rss_url.startswith("http"), f"{src.key} has invalid rss_url"

    def test_max_articles_positive(self):
        for src in AVAILABLE_SOURCES:
            assert src.max_articles > 0

    def test_expected_sources_present(self):
        keys = {s.key for s in AVAILABLE_SOURCES}
        expected = {"acm_technews", "mit_tech_review", "nytimes_tech", "bbc_tech"}
        assert expected == keys


# ---------------------------------------------------------------------------
# get_source_by_key
# ---------------------------------------------------------------------------

class TestGetSourceByKey:

    def test_returns_matching_source(self):
        src = get_source_by_key("bbc_tech")
        assert src is not None
        assert src.name == "BBC News — Technology"

    def test_returns_none_for_unknown_key(self):
        assert get_source_by_key("nonexistent") is None

    def test_returns_none_for_empty_string(self):
        assert get_source_by_key("") is None


# ---------------------------------------------------------------------------
# NewsSource dataclass
# ---------------------------------------------------------------------------

class TestNewsSourceDataclass:

    def test_default_max_articles(self):
        src = NewsSource(
            key="x", name="X", description="d", rss_url="https://x.com/rss"
        )
        assert src.max_articles == 5

    def test_custom_max_articles(self):
        src = NewsSource(
            key="x", name="X", description="d",
            rss_url="https://x.com/rss", max_articles=10,
        )
        assert src.max_articles == 10
