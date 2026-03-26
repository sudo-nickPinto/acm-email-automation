"""
Shared path helpers for cross-platform venv/runtime locations.
"""

from __future__ import annotations

import os
from pathlib import Path


def is_windows() -> bool:
    """Return True when running on Windows."""
    return os.name == "nt"


def venv_python_path(project_root: Path) -> Path:
    """Return the venv Python executable for the current OS."""
    if is_windows():
        return project_root / "venv" / "Scripts" / "python.exe"
    return project_root / "venv" / "bin" / "python3"


def venv_python_command(project_root: Path, target: str = "main.py") -> str:
    """Return a user-facing command string for invoking a file with the venv Python."""
    if is_windows():
        return f"venv\\Scripts\\python.exe {target}"
    return f"venv/bin/python3 {target}"
