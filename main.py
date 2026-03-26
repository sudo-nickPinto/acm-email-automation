# =============================================================================
# main.py — Orchestrator / Entry Point for News Digest (v2)
# =============================================================================
#
# This is the file you run to fetch and send your digest.
# It ties together the scraper and emailer into a simple pipeline:
#
#     fetch from all sources  →  check for duplicates  →  send email
#
# What changed from v1:
# ---------------------
# v1 only fetched ACM TechNews.  v2 fetches from every source the user
# selected in the setup wizard, and sends a multi-section digest.
#
# CLI flags:
#   --force    Send the email even if we already sent this edition
#   --dry-run  Print the plain-text digest to the terminal without sending
#
# Dependencies:
#   hashlib, sys, pathlib — all stdlib
#   newsdigest.scraper — multi-source RSS fetching
#   newsdigest.emailer — multi-source email formatting/sending
#   newsdigest.config  — loaded indirectly through scraper/emailer
# =============================================================================

#!/usr/bin/env python3
"""
News Digest Email Automation — main entry point.

Fetches articles from selected newspaper sources and emails a formatted digest.
"""

import hashlib
import sys
from datetime import date
from pathlib import Path

from newsdigest.scraper import fetch_all_sources, SourceResult, _is_published_today
from newsdigest.emailer import send_email, build_plain_text
from newsdigest.config import SELECTED_SOURCES

# Path to the state file that stores the hash of the last-sent edition.
STATE_FILE = Path(__file__).parent / ".last_sent"


def _results_hash(results: list[SourceResult]) -> str:
    """
    Create a SHA-256 hash of all article titles across all sources.

    This fingerprints the current set of articles so we can detect
    when the feeds haven't updated since the last send.
    """
    all_titles = []
    for result in results:
        for article in result.articles:
            all_titles.append(article.title)

    combined = f"{date.today().isoformat()}|" + "|".join(all_titles)
    return hashlib.sha256(combined.encode()).hexdigest()


def _already_sent(current_hash: str) -> bool:
    """
    Check if we already sent an email with this exact set of articles.
    """
    if not STATE_FILE.exists():
        return False
    stored = STATE_FILE.read_text().strip()
    return stored == current_hash


def _save_state(current_hash: str) -> None:
    """
    Persist the current edition's hash to disk.
    """
    STATE_FILE.write_text(current_hash)


def main():
    """
    Main execution flow:
      1. Parse CLI flags (--force, --dry-run)
      2. Validate that sources are configured
      3. Fetch articles from all selected sources
      4. Check for duplicate edition
      5. Either preview (dry run) or send the email
      6. Save state
    """
    force = "--force" in sys.argv
    dry_run = "--dry-run" in sys.argv

    # Validate configuration
    if not SELECTED_SOURCES:
        print("No news sources configured.")
        print("Run ./start.sh to set up your digest.")
        sys.exit(1)

    # Step 1: Fetch from all sources
    print("Fetching your news digest...")
    print()
    results = fetch_all_sources()

    # Step 1b: Filter to today's articles, flag stale sources
    for result in results:
        if result.error:
            continue
        fresh = [a for a in result.articles if _is_published_today(a.pub_date)]
        if not fresh and result.articles:
            # Source has articles but none published today
            result.no_new_today = True
        result.articles = fresh

    # Count totals after filtering
    total = sum(len(r.articles) for r in results)
    errors = sum(1 for r in results if r.error)
    stale = sum(1 for r in results if r.no_new_today)
    valid_sources = len(results) - errors

    print()
    if valid_sources == 0:
        print("No articles found from any source.")
        if errors > 0:
            print(f"{errors} source(s) had errors — check your internet connection.")
        sys.exit(1)

    if total == 0 and stale == 0:
        print("No articles found from any source.")
        sys.exit(1)

    if total > 0:
        print(f"Total: {total} new article(s) from {valid_sources - stale} source(s).")
    if stale > 0:
        print(f"{stale} source(s) had no new articles today.")

    # Step 2: Hash and check for duplicates
    current_hash = _results_hash(results)

    if not force and _already_sent(current_hash):
        print("Already sent this digest. No new articles since last send.")
        print("Use --force to resend, or wait for sources to update.")
        sys.exit(0)

    # Step 3a: Dry run — preview only
    if dry_run:
        print()
        print("--- DRY RUN (plain text preview) ---")
        print()
        print(build_plain_text(results))
        print()
        print("--- END DRY RUN ---")
        return  # Don't save state for dry runs

    # Step 3b: Send the email
    print()
    send_email(results)

    # Step 4: Save state
    _save_state(current_hash)

    print()
    print("Done!")


if __name__ == "__main__":
    main()
