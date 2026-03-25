"""
Tests for newsdigest.config — environment variable loading.

Uses monkeypatch to simulate different .env configurations.
"""

import os
from unittest.mock import patch


class TestConfigLoading:
    """Test that config.py correctly parses environment variables."""

    def _reload_config(self):
        """Force-reload the config module to pick up new env vars."""
        import importlib
        import newsdigest.config
        importlib.reload(newsdigest.config)
        return newsdigest.config

    @patch.dict(os.environ, {
        "SMTP_EMAIL": "user@gmail.com",
        "SMTP_APP_PASSWORD": "testpass",
        "SELECTED_SOURCES": "bbc_tech,nytimes_tech",
        "SCHEDULE_TIME": "09:00",
    }, clear=False)
    def test_loads_smtp_email(self):
        cfg = self._reload_config()
        assert cfg.SMTP_EMAIL == "user@gmail.com"

    @patch.dict(os.environ, {
        "SMTP_EMAIL": "user@gmail.com",
        "SMTP_APP_PASSWORD": "testpass",
        "SELECTED_SOURCES": "bbc_tech,nytimes_tech",
        "SCHEDULE_TIME": "09:00",
    }, clear=False)
    def test_loads_app_password(self):
        cfg = self._reload_config()
        assert cfg.SMTP_APP_PASSWORD == "testpass"

    @patch.dict(os.environ, {
        "SMTP_EMAIL": "user@gmail.com",
        "SMTP_APP_PASSWORD": "testpass",
        "SELECTED_SOURCES": "acm_technews,bbc_tech",
        "SCHEDULE_TIME": "",
    }, clear=False)
    def test_parses_selected_sources(self):
        cfg = self._reload_config()
        assert cfg.SELECTED_SOURCES == ["acm_technews", "bbc_tech"]

    @patch.dict(os.environ, {
        "SMTP_EMAIL": "user@gmail.com",
        "SMTP_APP_PASSWORD": "testpass",
        "SELECTED_SOURCES": "",
    }, clear=False)
    def test_empty_sources_gives_empty_list(self):
        cfg = self._reload_config()
        assert cfg.SELECTED_SOURCES == []

    @patch.dict(os.environ, {
        "SMTP_EMAIL": "user@gmail.com",
        "SMTP_APP_PASSWORD": "testpass",
        "SELECTED_SOURCES": "bbc_tech",
        "SCHEDULE_TIME": "14:30",
    }, clear=False)
    def test_schedule_time(self):
        cfg = self._reload_config()
        assert cfg.SCHEDULE_TIME == "14:30"

    @patch.dict(os.environ, {
        "SMTP_EMAIL": "sender@gmail.com",
        "SMTP_APP_PASSWORD": "p",
        "SELECTED_SOURCES": "bbc_tech",
        "RECIPIENT_EMAIL": "custom@gmail.com",
    }, clear=False)
    def test_recipient_can_be_overridden(self):
        cfg = self._reload_config()
        assert cfg.RECIPIENT_EMAIL == "custom@gmail.com"

    def test_smtp_server_constant(self):
        cfg = self._reload_config()
        assert cfg.SMTP_SERVER == "smtp.gmail.com"

    def test_smtp_port_constant(self):
        cfg = self._reload_config()
        assert cfg.SMTP_PORT == 587
