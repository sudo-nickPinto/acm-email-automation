# =============================================================================
# scheduler.py — Daily Schedule Installer (v3)
# =============================================================================
#
# Installs (or removes) a daily schedule so the digest is sent automatically
# without the user having to remember to run a command.
#
# Supports three operating systems:
#   macOS   → LaunchAgent plist in ~/Library/LaunchAgents/
#   Linux   → crontab entry (user-level, no sudo required)
#   Windows → Task Scheduler via schtasks.exe
#
# The schedule runs main.py once a day at the time the user chose.
# Logs go to the project's logs/ directory.
#
# Design decisions:
# -----------------
# - User-level only — no sudo, no system-wide changes
# - Each OS gets its own install/uninstall pair
# - detect_os() + dispatch keeps the public API clean
# - The plist/cron/task all invoke the venv python directly so the
#   schedule works even if the user's PATH changes
#
# Dependencies:
#   platform, subprocess, plistlib, pathlib — all stdlib
# =============================================================================

"""
Daily schedule installer — sets up automatic digest delivery
via macOS LaunchAgent, Linux cron, or Windows Task Scheduler.
"""

import os
import platform
import shlex
import subprocess
import sys
from pathlib import Path

from newsdigest.paths import venv_python_path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Unique identifier used across all platforms to name / find our schedule
SCHEDULE_LABEL = "com.newsdigest.daily"

# Project root — one level up from this file (newsdigest/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Full path to the venv python so the schedule doesn't depend on PATH
VENV_PYTHON = venv_python_path(PROJECT_ROOT)

MAIN_PY = PROJECT_ROOT / "main.py"
LOGS_DIR = PROJECT_ROOT / "logs"


def detect_os() -> str:
    """Return 'macos', 'linux', or 'windows'."""
    system = platform.system()
    if system == "Darwin":
        return "macos"
    elif system == "Linux":
        return "linux"
    elif system == "Windows":
        return "windows"
    return "unknown"


# =============================================================================
# macOS — LaunchAgent plist
# =============================================================================
# LaunchAgents are the macOS-native way to schedule recurring tasks for a
# single user.  A plist file lives in ~/Library/LaunchAgents/ and launchd
# executes it on the defined calendar interval.
# =============================================================================

def _macos_plist_path() -> Path:
    """Return the path where the LaunchAgent plist will live."""
    return Path.home() / "Library" / "LaunchAgents" / f"{SCHEDULE_LABEL}.plist"


def _macos_install(hour: int, minute: int) -> None:
    """
    Write a LaunchAgent plist and load it with launchctl.

    The plist tells macOS to run main.py every day at HH:MM.
    """
    plist_path = _macos_plist_path()

    # Build the plist XML (using string formatting instead of plistlib
    # because plistlib doesn't support StartCalendarInterval well)
    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{SCHEDULE_LABEL}</string>

    <key>ProgramArguments</key>
    <array>
        <string>{VENV_PYTHON}</string>
        <string>{MAIN_PY}</string>
    </array>

    <key>WorkingDirectory</key>
    <string>{PROJECT_ROOT}</string>

    <!-- Run every day at {hour:02d}:{minute:02d} -->
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>{hour}</integer>
        <key>Minute</key>
        <integer>{minute}</integer>
    </dict>

    <key>StandardOutPath</key>
    <string>{LOGS_DIR / "stdout.log"}</string>

    <key>StandardErrorPath</key>
    <string>{LOGS_DIR / "stderr.log"}</string>
</dict>
</plist>
"""

    # Ensure the LaunchAgents directory exists
    plist_path.parent.mkdir(parents=True, exist_ok=True)

    # Ensure logs directory exists
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    # Unload any existing schedule first (ignore errors if not loaded)
    if plist_path.exists():
        subprocess.run(
            ["launchctl", "unload", str(plist_path)],
            capture_output=True,
        )

    # Write the plist
    plist_path.write_text(plist_content)

    # Load it into launchd
    result = subprocess.run(
        ["launchctl", "load", str(plist_path)],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Failed to load LaunchAgent: {result.stderr.strip()}"
        )


def _macos_uninstall() -> None:
    """Unload and remove the LaunchAgent plist."""
    plist_path = _macos_plist_path()

    if plist_path.exists():
        subprocess.run(
            ["launchctl", "unload", str(plist_path)],
            capture_output=True,
        )
        plist_path.unlink()


def _macos_is_installed() -> bool:
    """Check if the LaunchAgent plist exists."""
    return _macos_plist_path().exists()


# =============================================================================
# Linux — crontab
# =============================================================================
# crontab is the standard Linux scheduling tool.  We add a single line to
# the user's crontab that runs main.py at the chosen time.  A comment tag
# makes our entry easy to find and remove later.
# =============================================================================

CRON_TAG = f"# {SCHEDULE_LABEL}"


def _linux_install(hour: int, minute: int) -> None:
    """
    Add a crontab entry that runs main.py daily at HH:MM.

    If an entry with our tag already exists, it's replaced.
    """
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    quoted_project_root = shlex.quote(str(PROJECT_ROOT))
    quoted_python = shlex.quote(str(VENV_PYTHON))
    quoted_main = shlex.quote(str(MAIN_PY))
    quoted_stdout = shlex.quote(str(LOGS_DIR / "stdout.log"))
    quoted_stderr = shlex.quote(str(LOGS_DIR / "stderr.log"))

    cron_line = (
        f"{minute} {hour} * * * "
        f"cd {quoted_project_root} && {quoted_python} {quoted_main} "
        f">> {quoted_stdout} 2>> {quoted_stderr} "
        f"{CRON_TAG}"
    )

    # Get the current crontab (empty string if none)
    result = subprocess.run(
        ["crontab", "-l"],
        capture_output=True,
        text=True,
    )
    existing = result.stdout if result.returncode == 0 else ""

    # Remove any existing newsdigest entry
    lines = [
        line for line in existing.splitlines()
        if CRON_TAG not in line
    ]

    # Add the new entry
    lines.append(cron_line)

    # Write back (pipe into crontab -)
    new_crontab = "\n".join(lines) + "\n"
    proc = subprocess.run(
        ["crontab", "-"],
        input=new_crontab,
        capture_output=True,
        text=True,
    )

    if proc.returncode != 0:
        raise RuntimeError(
            f"Failed to install crontab entry: {proc.stderr.strip()}"
        )


def _linux_uninstall() -> None:
    """Remove the newsdigest crontab entry."""
    result = subprocess.run(
        ["crontab", "-l"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return  # No crontab exists

    lines = [
        line for line in result.stdout.splitlines()
        if CRON_TAG not in line
    ]

    new_crontab = "\n".join(lines) + "\n" if lines else ""
    subprocess.run(
        ["crontab", "-"],
        input=new_crontab,
        capture_output=True,
        text=True,
    )


def _linux_is_installed() -> bool:
    """Check if our crontab entry exists."""
    result = subprocess.run(
        ["crontab", "-l"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return False
    return CRON_TAG in result.stdout


# =============================================================================
# Windows — Task Scheduler (schtasks.exe)
# =============================================================================
# schtasks.exe is built into Windows.  We create a daily scheduled task
# that runs main.py via the venv python at the chosen time.
# =============================================================================

def _windows_install(hour: int, minute: int) -> None:
    """
    Create a Windows Scheduled Task that runs main.py daily at HH:MM.

    Uses schtasks.exe which is available on all modern Windows versions.
    """
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    time_str = f"{hour:02d}:{minute:02d}"

    # Remove existing task first (ignore errors if it doesn't exist)
    subprocess.run(
        ["schtasks", "/Delete", "/TN", SCHEDULE_LABEL, "/F"],
        capture_output=True,
    )

    # Create the new task
    result = subprocess.run(
        [
            "schtasks", "/Create",
            "/TN", SCHEDULE_LABEL,
            "/TR", f'"{VENV_PYTHON}" "{MAIN_PY}"',
            "/SC", "DAILY",
            "/ST", time_str,
            "/F",  # Force overwrite if exists
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Failed to create scheduled task: {result.stderr.strip()}"
        )


def _windows_uninstall() -> None:
    """Remove the Windows Scheduled Task."""
    subprocess.run(
        ["schtasks", "/Delete", "/TN", SCHEDULE_LABEL, "/F"],
        capture_output=True,
    )


def _windows_is_installed() -> bool:
    """Check if the scheduled task exists."""
    result = subprocess.run(
        ["schtasks", "/Query", "/TN", SCHEDULE_LABEL],
        capture_output=True,
    )
    return result.returncode == 0


# =============================================================================
# Public API — OS-agnostic functions
# =============================================================================

def install_schedule(hour: int, minute: int) -> str:
    """
    Install a daily schedule for the current OS.

    Args:
        hour:   Hour to run (0-23)
        minute: Minute to run (0-59)

    Returns:
        Human-readable description of what was installed.

    Raises:
        RuntimeError: If the OS-specific install command fails.
        ValueError:   If the OS is not supported.
    """
    os_type = detect_os()

    if os_type == "macos":
        _macos_install(hour, minute)
        return f"macOS LaunchAgent installed — runs daily at {hour:02d}:{minute:02d}"
    elif os_type == "linux":
        _linux_install(hour, minute)
        return f"Cron job installed — runs daily at {hour:02d}:{minute:02d}"
    elif os_type == "windows":
        _windows_install(hour, minute)
        return f"Windows Scheduled Task installed — runs daily at {hour:02d}:{minute:02d}"
    else:
        raise ValueError(
            "Automatic scheduling is not supported on this OS. "
            "You can still run main.py manually."
        )


def uninstall_schedule() -> str:
    """
    Remove the daily schedule for the current OS.

    Returns:
        Human-readable description of what was removed.
    """
    os_type = detect_os()

    if os_type == "macos":
        _macos_uninstall()
        return "macOS LaunchAgent removed"
    elif os_type == "linux":
        _linux_uninstall()
        return "Cron job removed"
    elif os_type == "windows":
        _windows_uninstall()
        return "Windows Scheduled Task removed"
    else:
        return "No schedule to remove (unsupported OS)"


def is_schedule_installed() -> bool:
    """Check if a schedule is currently installed."""
    os_type = detect_os()

    if os_type == "macos":
        return _macos_is_installed()
    elif os_type == "linux":
        return _linux_is_installed()
    elif os_type == "windows":
        return _windows_is_installed()
    return False


# ---------------------------------------------------------------------------
# Standalone test — run with: venv/bin/python3 -m newsdigest.scheduler
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print(f"OS:        {detect_os()}")
    print(f"Project:   {PROJECT_ROOT}")
    print(f"Python:    {VENV_PYTHON}")
    print(f"Main:      {MAIN_PY}")
    print(f"Installed: {is_schedule_installed()}")
