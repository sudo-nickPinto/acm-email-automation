"""
Tests for newsdigest.cli — interactive menu system.

All I/O, subprocess calls, and file operations are mocked.
"""

import os
from pathlib import Path
from unittest.mock import patch, MagicMock, call

import pytest

from newsdigest.cli import (
    _read_env,
    _write_env,
    _reload_config,
    action_change_sources,
    action_change_email,
    action_change_password,
    action_change_schedule,
    action_status,
    action_send_now,
    action_preview,
    action_send_force,
    action_uninstall,
    show_menu,
    MENU_OPTIONS,
    PROJECT_ROOT,
    ENV_FILE,
)


# ---------------------------------------------------------------------------
# _read_env / _write_env
# ---------------------------------------------------------------------------

class TestEnvIO:

    def test_read_env_parses_key_value(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text(
            "# comment\n"
            "SMTP_EMAIL=user@gmail.com\n"
            "SMTP_APP_PASSWORD=abcdefghijklmnop\n"
            "SELECTED_SOURCES=bbc_tech,nytimes_tech\n"
        )
        with patch("newsdigest.cli.ENV_FILE", env_file):
            env = _read_env()
        assert env["SMTP_EMAIL"] == "user@gmail.com"
        assert env["SMTP_APP_PASSWORD"] == "abcdefghijklmnop"
        assert env["SELECTED_SOURCES"] == "bbc_tech,nytimes_tech"

    def test_read_env_skips_comments_and_blanks(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("# comment\n\nSMTP_EMAIL=a@gmail.com\n")
        with patch("newsdigest.cli.ENV_FILE", env_file):
            env = _read_env()
        assert "#" not in str(env.keys())
        assert env["SMTP_EMAIL"] == "a@gmail.com"

    def test_read_env_missing_file(self, tmp_path):
        env_file = tmp_path / ".env"
        with patch("newsdigest.cli.ENV_FILE", env_file):
            env = _read_env()
        assert env == {}

    def test_write_env_creates_file(self, tmp_path):
        env_file = tmp_path / ".env"
        with patch("newsdigest.cli.ENV_FILE", env_file):
            _write_env({
                "SMTP_EMAIL": "a@gmail.com",
                "SMTP_APP_PASSWORD": "abcdefghijklmnop",
                "RECIPIENT_EMAIL": "a@gmail.com",
                "SELECTED_SOURCES": "bbc_tech",
                "SCHEDULE_TIME": "08:00",
            })
        content = env_file.read_text()
        assert "SMTP_EMAIL=a@gmail.com" in content
        assert "SCHEDULE_TIME=08:00" in content

    def test_write_and_read_roundtrip(self, tmp_path):
        env_file = tmp_path / ".env"
        original = {
            "SMTP_EMAIL": "test@gmail.com",
            "SMTP_APP_PASSWORD": "testpasswordtest",
            "RECIPIENT_EMAIL": "test@gmail.com",
            "SELECTED_SOURCES": "acm_technews,bbc_tech",
            "SCHEDULE_TIME": "14:30",
        }
        with patch("newsdigest.cli.ENV_FILE", env_file):
            _write_env(original)
            result = _read_env()
        for key, value in original.items():
            assert result[key] == value


# ---------------------------------------------------------------------------
# action_change_email
# ---------------------------------------------------------------------------

class TestChangeEmail:

    @patch("newsdigest.cli._read_env", return_value={
        "SMTP_EMAIL": "old@gmail.com",
        "RECIPIENT_EMAIL": "old@gmail.com",
        "SMTP_APP_PASSWORD": "x",
        "SELECTED_SOURCES": "bbc_tech",
        "SCHEDULE_TIME": "",
    })
    @patch("newsdigest.cli._write_env")
    @patch("builtins.input", side_effect=["new@gmail.com", ""])
    def test_updates_email(self, mock_input, mock_write, mock_read):
        action_change_email()
        written = mock_write.call_args[0][0]
        assert written["SMTP_EMAIL"] == "new@gmail.com"
        assert written["RECIPIENT_EMAIL"] == "new@gmail.com"

    @patch("newsdigest.cli._read_env", return_value={"SMTP_EMAIL": "old@gmail.com"})
    @patch("newsdigest.cli._write_env")
    @patch("builtins.input", side_effect=["cancel", ""])
    def test_cancel_does_not_write(self, mock_input, mock_write, mock_read):
        action_change_email()
        mock_write.assert_not_called()

    @patch("newsdigest.cli._read_env", return_value={"SMTP_EMAIL": "old@gmail.com"})
    @patch("newsdigest.cli._write_env")
    @patch("builtins.input", side_effect=["bad-email", "good@gmail.com", ""])
    def test_rejects_invalid_email(self, mock_input, mock_write, mock_read):
        action_change_email()
        written = mock_write.call_args[0][0]
        assert written["SMTP_EMAIL"] == "good@gmail.com"


# ---------------------------------------------------------------------------
# action_change_password
# ---------------------------------------------------------------------------

class TestChangePassword:

    @patch("newsdigest.cli._read_env", return_value={
        "SMTP_EMAIL": "a@gmail.com",
        "SMTP_APP_PASSWORD": "oldpassoldpassol",
        "RECIPIENT_EMAIL": "a@gmail.com",
        "SELECTED_SOURCES": "bbc_tech",
        "SCHEDULE_TIME": "",
    })
    @patch("newsdigest.cli._write_env")
    @patch("builtins.input", side_effect=["abcdefghijklmnop", ""])
    def test_updates_password(self, mock_input, mock_write, mock_read):
        action_change_password()
        written = mock_write.call_args[0][0]
        assert written["SMTP_APP_PASSWORD"] == "abcdefghijklmnop"

    @patch("newsdigest.cli._read_env", return_value={"SMTP_APP_PASSWORD": "x"})
    @patch("newsdigest.cli._write_env")
    @patch("builtins.input", side_effect=["cancel", ""])
    def test_cancel_does_not_write(self, mock_input, mock_write, mock_read):
        action_change_password()
        mock_write.assert_not_called()

    @patch("newsdigest.cli._read_env", return_value={
        "SMTP_APP_PASSWORD": "x",
        "SMTP_EMAIL": "a@gmail.com",
        "RECIPIENT_EMAIL": "a@gmail.com",
        "SELECTED_SOURCES": "bbc_tech",
        "SCHEDULE_TIME": "",
    })
    @patch("newsdigest.cli._write_env")
    @patch("builtins.input", side_effect=["short", "has1number2here3", "abcdefghijklmnop", ""])
    def test_rejects_invalid_passwords(self, mock_input, mock_write, mock_read):
        action_change_password()
        written = mock_write.call_args[0][0]
        assert written["SMTP_APP_PASSWORD"] == "abcdefghijklmnop"


# ---------------------------------------------------------------------------
# action_change_sources
# ---------------------------------------------------------------------------

class TestChangeSources:

    @patch("newsdigest.cli._read_env", return_value={
        "SMTP_EMAIL": "a@gmail.com",
        "SMTP_APP_PASSWORD": "x",
        "RECIPIENT_EMAIL": "a@gmail.com",
        "SELECTED_SOURCES": "bbc_tech",
        "SCHEDULE_TIME": "",
    })
    @patch("newsdigest.cli._write_env")
    @patch("builtins.input", side_effect=["1 2", ""])
    def test_updates_sources(self, mock_input, mock_write, mock_read):
        action_change_sources()
        written = mock_write.call_args[0][0]
        assert "acm_technews" in written["SELECTED_SOURCES"]
        assert "mit_tech_review" in written["SELECTED_SOURCES"]

    @patch("newsdigest.cli._read_env", return_value={
        "SMTP_EMAIL": "a@gmail.com",
        "SMTP_APP_PASSWORD": "x",
        "RECIPIENT_EMAIL": "a@gmail.com",
        "SELECTED_SOURCES": "",
        "SCHEDULE_TIME": "",
    })
    @patch("newsdigest.cli._write_env")
    @patch("builtins.input", side_effect=["all", ""])
    def test_all_keyword(self, mock_input, mock_write, mock_read):
        action_change_sources()
        written = mock_write.call_args[0][0]
        assert "acm_technews" in written["SELECTED_SOURCES"]
        assert "bbc_tech" in written["SELECTED_SOURCES"]

    @patch("newsdigest.cli._read_env", return_value={
        "SMTP_EMAIL": "a@gmail.com",
        "SMTP_APP_PASSWORD": "x",
        "RECIPIENT_EMAIL": "a@gmail.com",
        "SELECTED_SOURCES": "bbc_tech",
        "SCHEDULE_TIME": "",
    })
    @patch("newsdigest.cli._write_env")
    @patch("builtins.input", side_effect=["", "99", "1", ""])
    def test_rejects_empty_and_invalid(self, mock_input, mock_write, mock_read):
        action_change_sources()
        mock_write.assert_called_once()


# ---------------------------------------------------------------------------
# action_change_schedule
# ---------------------------------------------------------------------------

class TestChangeSchedule:

    @patch("newsdigest.cli._read_env", return_value={
        "SMTP_EMAIL": "a@gmail.com",
        "SMTP_APP_PASSWORD": "x",
        "RECIPIENT_EMAIL": "a@gmail.com",
        "SELECTED_SOURCES": "bbc_tech",
        "SCHEDULE_TIME": "",
    })
    @patch("newsdigest.cli._write_env")
    @patch("newsdigest.scheduler.detect_os", return_value="macos")
    @patch("newsdigest.scheduler._macos_install")
    @patch("newsdigest.scheduler.is_schedule_installed", return_value=False)
    @patch("builtins.input", side_effect=["1", "09:30", ""])
    def test_set_new_time(self, mock_input, mock_installed, mock_install,
                          mock_detect, mock_write, mock_read):
        action_change_schedule()
        written = mock_write.call_args[0][0]
        assert written["SCHEDULE_TIME"] == "09:30"

    @patch("newsdigest.cli._read_env", return_value={
        "SMTP_EMAIL": "a@gmail.com",
        "SMTP_APP_PASSWORD": "x",
        "RECIPIENT_EMAIL": "a@gmail.com",
        "SELECTED_SOURCES": "bbc_tech",
        "SCHEDULE_TIME": "08:00",
    })
    @patch("newsdigest.cli._write_env")
    @patch("newsdigest.scheduler.detect_os", return_value="macos")
    @patch("newsdigest.scheduler._macos_uninstall")
    @patch("newsdigest.scheduler.is_schedule_installed", return_value=True)
    @patch("builtins.input", side_effect=["2", ""])
    def test_turn_off_schedule(self, mock_input, mock_installed, mock_uninstall,
                               mock_detect, mock_write, mock_read):
        action_change_schedule()
        written = mock_write.call_args[0][0]
        assert written["SCHEDULE_TIME"] == ""

    @patch("newsdigest.cli._read_env", return_value={
        "SMTP_EMAIL": "a@gmail.com",
        "SMTP_APP_PASSWORD": "x",
        "RECIPIENT_EMAIL": "a@gmail.com",
        "SELECTED_SOURCES": "bbc_tech",
        "SCHEDULE_TIME": "08:00",
    })
    @patch("newsdigest.cli._write_env")
    @patch("newsdigest.scheduler.is_schedule_installed", return_value=True)
    @patch("builtins.input", side_effect=["0", ""])
    def test_cancel(self, mock_input, mock_installed, mock_write, mock_read):
        action_change_schedule()
        mock_write.assert_not_called()


# ---------------------------------------------------------------------------
# action_send_now / action_preview / action_send_force
# ---------------------------------------------------------------------------

class TestSendActions:

    @patch("newsdigest.cli.subprocess.run")
    @patch("builtins.input", return_value="")
    def test_send_now_calls_main(self, mock_input, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        action_send_now()
        args = mock_run.call_args[0][0]
        assert "main.py" in args[-1]
        assert "--dry-run" not in args
        assert "--force" not in args

    @patch("newsdigest.cli.subprocess.run")
    @patch("builtins.input", return_value="")
    def test_preview_uses_dry_run(self, mock_input, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        action_preview()
        args = mock_run.call_args[0][0]
        assert "--dry-run" in args

    @patch("newsdigest.cli.subprocess.run")
    @patch("builtins.input", return_value="")
    def test_force_send_uses_force(self, mock_input, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        action_send_force()
        args = mock_run.call_args[0][0]
        assert "--force" in args


# ---------------------------------------------------------------------------
# action_status
# ---------------------------------------------------------------------------

class TestStatus:

    @patch("newsdigest.cli._read_env", return_value={
        "SMTP_EMAIL": "user@gmail.com",
        "SELECTED_SOURCES": "bbc_tech,nytimes_tech",
        "SCHEDULE_TIME": "08:00",
    })
    @patch("newsdigest.scheduler.is_schedule_installed", return_value=True)
    @patch("newsdigest.cli.subprocess.run")
    @patch("builtins.input", return_value="")
    def test_status_runs_without_error(self, mock_input, mock_run, mock_sched, mock_read):
        mock_run.return_value = MagicMock(stdout="Python 3.13.7", returncode=0)
        # Should not raise
        action_status()


# ---------------------------------------------------------------------------
# action_uninstall
# ---------------------------------------------------------------------------

class TestUninstall:

    @patch("newsdigest.scheduler.is_schedule_installed", return_value=False)
    @patch("newsdigest.cli.os.path.islink", return_value=False)
    @patch("newsdigest.cli.os.remove")
    @patch("builtins.input", side_effect=["n"])
    def test_cancel_does_nothing(self, mock_input, mock_remove, mock_islink, mock_sched):
        # Should not raise or call rmtree
        action_uninstall()
        mock_remove.assert_not_called()

    @patch("newsdigest.scheduler.is_schedule_installed", return_value=True)
    @patch("newsdigest.scheduler.uninstall_schedule")
    @patch("newsdigest.cli.os.path.islink", return_value=False)
    @patch("newsdigest.cli.os.remove")
    @patch("shutil.rmtree")
    @patch("builtins.input", side_effect=["y"])
    def test_confirm_uninstall(self, mock_input, mock_rmtree, mock_remove,
                                mock_islink, mock_unsched, mock_sched):
        with pytest.raises(SystemExit):
            action_uninstall()
        mock_unsched.assert_called_once()
        mock_rmtree.assert_called_once()


# ---------------------------------------------------------------------------
# show_menu
# ---------------------------------------------------------------------------

class TestShowMenu:

    @patch("newsdigest.cli._read_env", return_value={"SMTP_EMAIL": "a@gmail.com", "SCHEDULE_TIME": ""})
    @patch("builtins.input", side_effect=["0"])
    def test_exit_on_zero(self, mock_input, mock_read):
        show_menu()  # Should return cleanly

    @patch("newsdigest.cli._read_env", return_value={"SMTP_EMAIL": "a@gmail.com", "SCHEDULE_TIME": ""})
    @patch("builtins.input", side_effect=["8", "", "0"])
    def test_dispatches_to_status(self, mock_input, mock_read):
        """Option 8 runs action_status (verified by reaching the pause prompt)."""
        # action_status runs for real but _read_env is mocked, so it won't
        # fail. The three inputs are: "8" (choose status), "" (pause after
        # status), "0" (exit menu).
        with patch("newsdigest.cli.subprocess.run",
                    return_value=MagicMock(stdout="Python 3.13.7", returncode=0)):
            with patch("newsdigest.scheduler.is_schedule_installed", return_value=False):
                show_menu()

    @patch("newsdigest.cli._read_env", return_value={"SMTP_EMAIL": "a@gmail.com", "SCHEDULE_TIME": ""})
    @patch("builtins.input", side_effect=["invalid", "", "0"])
    def test_handles_invalid_input(self, mock_input, mock_read):
        show_menu()  # Should not crash

    def test_menu_options_count(self):
        assert len(MENU_OPTIONS) == 10  # options 0-9

    def test_exit_option_has_no_action(self):
        exit_opt = [opt for opt in MENU_OPTIONS if opt[0] == "0"]
        assert len(exit_opt) == 1
        assert exit_opt[0][2] is None
