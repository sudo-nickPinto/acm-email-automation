"""
Tests for newsdigest.scheduler — daily schedule install/uninstall.

All subprocess and OS calls are mocked.
"""

from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import shlex

from newsdigest.scheduler import (
    detect_os,
    install_schedule,
    uninstall_schedule,
    is_schedule_installed,
    SCHEDULE_LABEL,
    CRON_TAG,
    _macos_plist_path,
    PROJECT_ROOT,
    VENV_PYTHON,
    MAIN_PY,
    LOGS_DIR,
)


# ---------------------------------------------------------------------------
# detect_os
# ---------------------------------------------------------------------------

class TestDetectOs:

    @patch("newsdigest.scheduler.platform.system", return_value="Darwin")
    def test_macos(self, _):
        assert detect_os() == "macos"

    @patch("newsdigest.scheduler.platform.system", return_value="Linux")
    def test_linux(self, _):
        assert detect_os() == "linux"

    @patch("newsdigest.scheduler.platform.system", return_value="Windows")
    def test_windows(self, _):
        assert detect_os() == "windows"

    @patch("newsdigest.scheduler.platform.system", return_value="FreeBSD")
    def test_unknown(self, _):
        assert detect_os() == "unknown"


# ---------------------------------------------------------------------------
# install_schedule (dispatch + OS-specific mock)
# ---------------------------------------------------------------------------

class TestInstallSchedule:

    @patch("newsdigest.scheduler.detect_os", return_value="macos")
    @patch("newsdigest.scheduler._macos_install")
    def test_macos_dispatch(self, mock_install, _):
        msg = install_schedule(8, 30)
        mock_install.assert_called_once_with(8, 30)
        assert "LaunchAgent" in msg
        assert "08:30" in msg

    @patch("newsdigest.scheduler.detect_os", return_value="linux")
    @patch("newsdigest.scheduler._linux_install")
    def test_linux_dispatch(self, mock_install, _):
        msg = install_schedule(7, 0)
        mock_install.assert_called_once_with(7, 0)
        assert "Cron" in msg
        assert "07:00" in msg

    @patch("newsdigest.scheduler.detect_os", return_value="windows")
    @patch("newsdigest.scheduler._windows_install")
    def test_windows_dispatch(self, mock_install, _):
        msg = install_schedule(9, 15)
        mock_install.assert_called_once_with(9, 15)
        assert "Scheduled Task" in msg
        assert "09:15" in msg

    @patch("newsdigest.scheduler.detect_os", return_value="unknown")
    def test_unknown_os_raises(self, _):
        import pytest
        with pytest.raises(ValueError, match="not supported"):
            install_schedule(8, 0)


# ---------------------------------------------------------------------------
# uninstall_schedule
# ---------------------------------------------------------------------------

class TestUninstallSchedule:

    @patch("newsdigest.scheduler.detect_os", return_value="macos")
    @patch("newsdigest.scheduler._macos_uninstall")
    def test_macos_uninstall(self, mock_uninstall, _):
        msg = uninstall_schedule()
        mock_uninstall.assert_called_once()
        assert "LaunchAgent" in msg

    @patch("newsdigest.scheduler.detect_os", return_value="linux")
    @patch("newsdigest.scheduler._linux_uninstall")
    def test_linux_uninstall(self, mock_uninstall, _):
        msg = uninstall_schedule()
        mock_uninstall.assert_called_once()
        assert "Cron" in msg

    @patch("newsdigest.scheduler.detect_os", return_value="windows")
    @patch("newsdigest.scheduler._windows_uninstall")
    def test_windows_uninstall(self, mock_uninstall, _):
        msg = uninstall_schedule()
        mock_uninstall.assert_called_once()
        assert "Scheduled Task" in msg

    @patch("newsdigest.scheduler.detect_os", return_value="unknown")
    def test_unknown_os_returns_message(self, _):
        msg = uninstall_schedule()
        assert "unsupported" in msg.lower() or "No schedule" in msg


# ---------------------------------------------------------------------------
# is_schedule_installed
# ---------------------------------------------------------------------------

class TestIsScheduleInstalled:

    @patch("newsdigest.scheduler.detect_os", return_value="macos")
    @patch("newsdigest.scheduler._macos_is_installed", return_value=True)
    def test_macos_installed(self, *_):
        assert is_schedule_installed() is True

    @patch("newsdigest.scheduler.detect_os", return_value="macos")
    @patch("newsdigest.scheduler._macos_is_installed", return_value=False)
    def test_macos_not_installed(self, *_):
        assert is_schedule_installed() is False

    @patch("newsdigest.scheduler.detect_os", return_value="unknown")
    def test_unknown_os_returns_false(self, _):
        assert is_schedule_installed() is False


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

class TestConstants:

    def test_schedule_label(self):
        assert SCHEDULE_LABEL == "com.newsdigest.daily"

    def test_cron_tag_contains_label(self):
        assert SCHEDULE_LABEL in CRON_TAG

    def test_plist_path_contains_label(self):
        path = _macos_plist_path()
        assert SCHEDULE_LABEL in str(path)
        assert str(path).endswith(".plist")


class TestLinuxCronQuoting:

    @patch("newsdigest.scheduler.subprocess.run")
    def test_linux_install_quotes_paths(self, mock_run):
        mock_run.side_effect = [
            MagicMock(returncode=1, stdout=""),
            MagicMock(returncode=0, stderr=""),
        ]

        from newsdigest.scheduler import _linux_install

        _linux_install(8, 30)

        install_call = mock_run.call_args_list[1]
        cron_text = install_call.kwargs["input"]
        expected = (
            f"30 8 * * * cd {shlex.quote(str(PROJECT_ROOT))} && "
            f"{shlex.quote(str(VENV_PYTHON))} {shlex.quote(str(MAIN_PY))} "
            f">> {shlex.quote(str(LOGS_DIR / 'stdout.log'))} "
            f"2>> {shlex.quote(str(LOGS_DIR / 'stderr.log'))} "
            f"{CRON_TAG}\n"
        )
        assert cron_text == expected
