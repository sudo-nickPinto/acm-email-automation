# =============================================================================
# main.py — Orchestrator / Entry Point for ACM TechNews Email Automation
# =============================================================================
#
# This is the file you run.  It ties together the scraper and the emailer
# into a simple pipeline:
#
#     fetch articles  →  check for duplicates  →  send email
#
# Why a separate main.py?
# -----------------------
# In software engineering, the "entry point" should be thin — it coordinates
# other modules but contains minimal logic itself.  If scraping logic lived
# here, and emailing logic lived here, this file would be a tangled mess.
# Instead, main.py is a ~60-line conductor: it calls fetch_articles(), makes
# a decision (new edition or duplicate?), then calls send_email().
#
# Duplicate detection:
# --------------------
# ACM TechNews publishes roughly 3 times a week (Mon/Wed/Fri).  If our
# scheduled job fires but the feed hasn't updated yet, we don't want to
# spam the recipient with the same articles.  We solve this by hashing the
# article titles with SHA-256 and storing the hash in a .last_sent file.
# On the next run, if the hash matches, we skip sending.
#
# CLI flags:
#   --force    Send the email even if we already sent this edition
#   --dry-run  Print the plain-text email to the terminal without sending
#
# Dependencies:
#   hashlib, json, os, sys, pathlib — all stdlib
#   acm_technews.scraper — our RSS feed module
#   acm_technews.emailer — our email formatting/sending module
# =============================================================================

#!/usr/bin/env python3
"""
ACM TechNews Email Automation — main entry point.

Fetches the latest ACM TechNews articles and emails a formatted digest.
"""

# hashlib provides SHA-256 hashing, which we use to fingerprint article lists
import hashlib

# json is imported but currently unused — it was included for potential future
# state serialization (e.g., storing more than just a hash in .last_sent)
import json

# os provides operating system utilities (not heavily used here since we
# prefer pathlib, but available for path joins and env access if needed)
import os

# sys gives us access to command-line arguments (sys.argv) and the ability
# to exit with a status code (sys.exit)
import sys

# Path is an object-oriented filepath handler that makes file operations
# cleaner than raw string manipulation with os.path
from pathlib import Path

# Import the scraper function — this does the HTTP request and XML parsing
from acm_technews.scraper import fetch_articles

# Import the email sender — this formats articles into HTML/text and sends
from acm_technews.emailer import send_email

# Path to the state file that stores the hash of the last-sent edition.
# We put it in the same directory as main.py (using __file__ to find that
# directory regardless of where the script is invoked from).
STATE_FILE = Path(__file__).parent / ".last_sent"


def _articles_hash(articles) -> str:
    """
    Create a SHA-256 hash of all article titles, joined by pipes.

    This serves as a fingerprint for a particular edition of TechNews.
    If the titles haven't changed, the hash will be identical, and we
    know we've already sent this edition.

    Example:
        articles with titles ["AI in Healthcare", "Quantum Advances"]
        → SHA-256 of "AI in Healthcare|Quantum Advances"
        → "a3f2c8..."
    """
    # Join all titles with | as a delimiter, then hash the result
    titles = "|".join(a.title for a in articles)
    return hashlib.sha256(titles.encode()).hexdigest()


def _already_sent(current_hash: str) -> bool:
    """
    Check if we already sent an email for this exact edition.

    Reads the stored hash from .last_sent and compares it to the
    current hash.  Returns True if they match (meaning: don't send).
    """
    # If the state file doesn't exist, we've never sent anything
    if not STATE_FILE.exists():
        return False

    # Read the stored hash and compare (strip whitespace just in case)
    stored = STATE_FILE.read_text().strip()
    return stored == current_hash


def _save_state(current_hash: str) -> None:
    """
    Persist the current edition's hash to disk so future runs can
    detect duplicates.  Overwrites any previous content.
    """
    STATE_FILE.write_text(current_hash)


def main():
    """
    Main execution flow:
      1. Parse CLI flags (--force, --dry-run)
      2. Fetch articles from the RSS feed
      3. Check for duplicate edition (skip if already sent)
      4. Either preview (dry run) or send the email
      5. Save state so we don't re-send
    """
    # Check if --force was passed as a command-line argument.
    # --force bypasses the duplicate check and sends regardless.
    force = "--force" in sys.argv

    # Check if --dry-run was passed.
    # --dry-run prints the email to the terminal without actually sending it.
    dry_run = "--dry-run" in sys.argv

    # Step 1: Fetch articles from the ACM TechNews RSS feed
    print("Fetching ACM TechNews...")
    articles = fetch_articles()

    # If no articles came back, the feed might be down or empty
    if not articles:
        print("No articles found. The RSS feed may be empty or unavailable.")
        # Exit with code 1 to signal failure (useful for monitoring)
        sys.exit(1)

    print(f"Found {len(articles)} articles.")

    # Step 2: Hash the current articles to create a fingerprint
    current_hash = _articles_hash(articles)

    # Step 3: Skip if we already sent this edition (unless --force)
    if not force and _already_sent(current_hash):
        print("Already sent email for this edition. Use --force to resend.")
        sys.exit(0)  # Exit 0 = success, just nothing to do

    # Step 4a: Dry run mode — preview only, no email sent
    if dry_run:
        # Import build_plain_text here (lazy import) since it's only needed
        # for dry runs, not for every execution
        from acm_technews.emailer import build_plain_text
        print("\n--- DRY RUN (plain text preview) ---\n")
        print(build_plain_text(articles))
        print("\n--- END DRY RUN ---")
        return  # Don't save state — dry runs shouldn't count as "sent"

    # Step 4b: Actually send the email
    send_email(articles)

    # Step 5: Save the hash so we don't re-send this same edition
    _save_state(current_hash)

    print("Done!")


# ---------------------------------------------------------------------------
# Standard Python idiom: only run main() when this file is executed directly.
# If someone imports main.py as a module (rare, but possible), main() won't
# run automatically — they'd have to call it explicitly.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    main()
