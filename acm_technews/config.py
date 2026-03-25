# =============================================================================
# config.py — Central Configuration Module
# =============================================================================
#
# This file is the single source of truth for every configurable value in the
# project.  Rather than scatter os.getenv() calls throughout the codebase, we
# load everything here once at import time and expose plain module-level
# constants that the rest of the application can import by name.
#
# Why a dedicated config file?
# ----------------------------
# 1. Separation of concerns — business logic (scraper, emailer) should never
#    know *how* configuration is loaded.  It might come from environment
#    variables today, but tomorrow it could come from AWS Secrets Manager or a
#    YAML file.  This module is the only place that needs to change.
# 2. Security — sensitive values (passwords, API keys) live in a .env file
#    that is git-ignored.  python-dotenv reads that file and injects the
#    values into the process environment so os.getenv() can find them.
# 3. Fail-fast — if a required variable is missing we will get a clear None
#    here rather than a confusing error deep inside smtplib.
#
# How it works:
#   scraper.py  ── imports ACM_TECHNEWS_URL from here
#   emailer.py  ── imports SMTP_* and RECIPIENT_EMAIL from here
#   main.py     ── doesn't import config directly, but its dependencies do
#
# Dependencies:
#   python-dotenv — reads key=value pairs from .env into os.environ
#   os (stdlib)   — reads environment variables
# =============================================================================

# os gives us access to environment variables via os.getenv()
import os

# load_dotenv reads the .env file (in the project root) and pushes each
# key=value pair into the current process's environment variables so that
# os.getenv() can retrieve them.  If no .env file exists it silently does
# nothing, which is fine for production environments that set real env vars.
from dotenv import load_dotenv

# Actually execute the .env loading.  This must happen before any os.getenv()
# calls below, otherwise the variables won't be available yet.
load_dotenv()

# ---------------------------------------------------------------------------
# SMTP (Simple Mail Transfer Protocol) settings
# ---------------------------------------------------------------------------
# These configure how we authenticate with Gmail's outgoing mail server.
# SMTP_EMAIL is the Gmail address that will appear in the "From" field.
SMTP_EMAIL = os.getenv("SMTP_EMAIL")

# Gmail requires an "App Password" when 2-Factor Auth is enabled.
# A regular account password will be rejected.
SMTP_APP_PASSWORD = os.getenv("SMTP_APP_PASSWORD")

# Gmail's SMTP host.  All Gmail users connect to the same server.
SMTP_SERVER = "smtp.gmail.com"

# Port 587 is the standard STARTTLS submission port.  The connection starts
# unencrypted, then upgrades to TLS after the STARTTLS command.
# (Port 465 is the older implicit-TLS port; 587 is preferred.)
SMTP_PORT = 587

# ---------------------------------------------------------------------------
# Recipient
# ---------------------------------------------------------------------------
# Who receives the digest email.  Must be set in .env — there is no default
# to avoid accidentally emailing a stranger.
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")

# ---------------------------------------------------------------------------
# ACM TechNews
# ---------------------------------------------------------------------------
# Public URL for the human-readable TechNews page.  Not currently used by the
# scraper (which hits the RSS XML feed directly) but kept here as a reference
# and for potential future use in email footers.
ACM_TECHNEWS_URL = "https://technews.acm.org/"
