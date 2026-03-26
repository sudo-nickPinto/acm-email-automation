"""
Tests for cross-platform path helpers.
"""

from pathlib import Path
from unittest.mock import patch

from newsdigest.paths import venv_python_path, venv_python_command


class TestVenvPythonPath:

    def test_posix_path(self):
        with patch("newsdigest.paths.is_windows", return_value=False):
            assert venv_python_path(Path("/tmp/project")) == Path("/tmp/project/venv/bin/python3")

    def test_windows_path(self):
        with patch("newsdigest.paths.is_windows", return_value=True):
            assert venv_python_path(Path("C:/project")) == Path("C:/project/venv/Scripts/python.exe")


class TestVenvPythonCommand:

    def test_posix_command(self):
        with patch("newsdigest.paths.is_windows", return_value=False):
            assert venv_python_command(Path("/tmp/project")) == "venv/bin/python3 main.py"

    def test_windows_command(self):
        with patch("newsdigest.paths.is_windows", return_value=True):
            assert venv_python_command(Path("C:/project")) == r"venv\Scripts\python.exe main.py"
