# Lab 05: Simulate a Failure

## Goal

Practice reasoning about failure modes in the system.  Choose one
scenario and trace through the code to understand exactly what happens.

---

## Scenario A: RSS Feed Timeout

**The situation:** BBC's RSS server doesn't respond within 30 seconds.

**Trace through the code:**

1. `scraper.py` → `_fetch_single_source()` calls `requests.get(url, timeout=30)`
2. After 30s, `requests.Timeout` is raised
3. Caught by the `except requests.Timeout` handler
4. Returns `SourceResult(source=source, error="Timed out after 30s")`
5. `fetch_all_sources()` prints `⚠ BBC News: Timed out after 30s`
6. **Other sources still work** — the timeout is per-source

**Verify:** Mock it in a test (see `test_scraper.py::test_timeout_returns_error`)

---

## Scenario B: Wrong Gmail Password

**The situation:** User entered an invalid App Password.

1. `emailer.py` → `send_email()` calls `server.login(email, password)`
2. Gmail rejects: `smtplib.SMTPAuthenticationError`
3. This exception is **not caught** in `send_email()` — it propagates up
4. `main.py` crashes with a traceback

**Why not catch it?** Because there's nothing useful to do automatically.
The user needs to fix their credentials.

**Fix:** `news-digest` → Option 6 → Enter correct App Password

---

## Scenario C: Empty Source Selection

**The situation:** `.env` has `SELECTED_SOURCES=` (empty).

1. `config.py` parses → `SELECTED_SOURCES = []` (empty list)
2. `main.py` checks: `if not SELECTED_SOURCES: sys.exit(1)`
3. User sees: `"No news sources configured. Run ./start.sh to set up."`

**This is the fastest failure** — before any network calls.

---

## Scenario D: Checksum Mismatch (Installer)

**The situation:** Downloaded zip is corrupted or tampered with.

1. Installer downloads `news-digest.zip` and `SHA256SUMS.txt`
2. Computes SHA-256 of the zip
3. Compares against expected hash from `SHA256SUMS.txt`
4. **Mismatch** → installer prints `CHECKSUM MISMATCH` and exits immediately
5. **No extraction happens** — the corrupted/tampered zip is never opened

---

## Scenario E: No Python Found

**The situation:** User's machine doesn't have Python 3 installed.

1. `start.sh` checks for `python3` on PATH
2. Not found → offers installation guidance:
   - macOS: `brew install python3`
   - Linux: `sudo apt install python3`
3. Exits with an error message

---

## Your Task

1. Pick a scenario above (or invent your own)
2. Open the relevant source file
3. Find the exact line where the failure is detected
4. Find the exact error message the user sees
5. Find the safest recovery step
6. Check if there's a test for this failure mode in `tests/`
