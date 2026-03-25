# =============================================================================
# config.py — Central Configuration Module (v3)
# =============================================================================
#
# Single source of truth for every configurable value in the project.
# Loads settings from .env (written by the setup wizard) and exposes
# them as plain module-level constants.
#
# What changed from v2:
# ---------------------
# - Added SCHEDULE_TIME — the daily delivery time (e.g., "08:00") if
#   the user opted into automatic scheduling, or "" if not
#
# Dependencies:
#   python-dotenv — reads key=value pairs from .env into os.environ
#   os (stdlib)   — reads environment variables
# =============================================================================

"""
Configuration module — loads .env and exposes settings as constants.
"""

import os
from dotenv import load_dotenv

# Load .env file into the process environment.
# This must happen before any os.getenv() calls below.
load_dotenv()

# ---------------------------------------------------------------------------
# SMTP (email sending) settings
# ---------------------------------------------------------------------------

# The Gmail address that sends the digest email
SMTP_EMAIL: str | None = os.getenv("SMTP_EMAIL")

# Gmail App Password (NOT the regular account password).
# Requires 2-Factor Authentication to be enabled on the Google account.
SMTP_APP_PASSWORD: str | None = os.getenv("SMTP_APP_PASSWORD")

# Gmail's SMTP server — same for all Gmail users
SMTP_SERVER: str = "smtp.gmail.com"

# Port 587 = STARTTLS (starts unencrypted, upgrades to TLS)
SMTP_PORT: int = 587

# ---------------------------------------------------------------------------
# Recipient settings
# ---------------------------------------------------------------------------

# Who receives the digest email.  Defaults to the sender's own address
# (most users will email themselves), but can be overridden in .env.
RECIPIENT_EMAIL: str | None = os.getenv("RECIPIENT_EMAIL", os.getenv("SMTP_EMAIL"))

# ---------------------------------------------------------------------------
# Source selection
# ---------------------------------------------------------------------------

# Comma-separated list of source keys the user selected in the wizard.
# Example: "acm_technews,bbc_tech,nytimes_tech"
SELECTED_SOURCES_RAW: str = os.getenv("SELECTED_SOURCES", "")

# Parse into a clean list of key strings
SELECTED_SOURCES: list[str] = [
    s.strip() for s in SELECTED_SOURCES_RAW.split(",") if s.strip()
]

# ---------------------------------------------------------------------------
# Schedule settings
# ---------------------------------------------------------------------------

# The time the daily digest is scheduled to send (e.g., "08:00").
# Empty string means no automatic scheduling — user runs main.py manually.
SCHEDULE_TIME: str = os.getenv("SCHEDULE_TIME", "")
