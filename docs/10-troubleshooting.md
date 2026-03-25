# 10 — Troubleshooting Guide

## Quick Diagnosis Flowchart

```
Email didn't arrive?
  │
  ├── Did you run the setup wizard?
  │     └── No → Run: ./start.sh
  │
  ├── Run: venv/bin/python3 main.py
  │     │
  │     ├── "No news sources configured"
  │     │     └── Run ./start.sh and select your sources
  │     │
  │     ├── "Already sent this digest"
  │     │     └── Not an error! Use --force to resend
  │     │
  │     ├── "No articles found from any source"
  │     │     └── RSS feeds may be temporarily down; try again later
  │     │
  │     ├── "SMTPAuthenticationError"
  │     │     └── App Password is wrong or expired (see fix #2 below)
  │     │
  │     ├── "ConnectionRefusedError" / "ConnectionError"
  │     │     └── Check your internet connection
  │     │
  │     └── Some sources show ⚠ warnings
  │           └── Those specific feeds are temporarily down; others still work
  │
  └── Command not found?
        └── Close and reopen your terminal, then try: ./start.sh
```

---

## Common Issues and Fixes

### 1. "No news sources configured"

**What happened:** The `.env` file is missing or doesn't have `SELECTED_SOURCES`.

**Fix:** Run the setup wizard:
```bash
./start.sh
```

---

### 2. `SMTPAuthenticationError: (535, b'5.7.8 Username and Password not accepted')`

**What happened:** Gmail rejected the login credentials.

**Possible causes:**
1. The App Password in `.env` is wrong
2. The App Password was revoked in Google account settings
3. You're using your regular Gmail password instead of an App Password
4. 2-Step Verification is not enabled on the Gmail account

**Fix:**
1. Go to [Google App Passwords](https://myaccount.google.com/apppasswords)
2. Generate a new App Password
3. Re-run `./start.sh` to enter the new password
4. Test: `venv/bin/python3 main.py --dry-run`

---

### 3. "Already sent this digest"

**What happened:** The feeds haven't updated since your last send. The duplicate detection is working correctly.

**Fix:** Wait for new articles, or force a resend:
```bash
venv/bin/python3 main.py --force
```

To reset all state:
```bash
# Remove the state file (it only stores a hash, nothing sensitive)
cat /dev/null > .last_sent
```

---

### 4. Some sources show warnings (⚠) but others work

**What happened:** One or more RSS feeds are temporarily unavailable. The other sources still delivered their articles.

**This is expected behavior.** The scraper handles each source independently — one failure doesn't affect the others. The warning appears in your email so you know which source was skipped.

**If a source is consistently failing:**
- The RSS feed URL may have changed
- Check the source's website to see if they still publish an RSS feed
- The feed URL is defined in `newsdigest/sources.py`

---

### 5. "No articles found from any source"

**What happened:** Every feed returned zero articles or every fetch failed.

**Possible causes:**
- No internet connection
- All feed servers are down simultaneously (rare)

**Diagnosis:**
```bash
# Preview what the scraper fetches
venv/bin/python3 -m newsdigest.scraper
```

---

### 6. Python not found after installation

**What happened:** You installed Python, but the terminal can't find it yet.

**Fix:** Close and reopen your terminal application, then run `./start.sh` again. The terminal needs to reload its PATH to find newly installed programs.

---

### 7. `ModuleNotFoundError: No module named 'requests'`

**What happened:** Dependencies aren't installed in the virtual environment.

**Fix:**
```bash
venv/bin/pip install -r requirements.txt
```

Or, if the venv doesn't exist:
```bash
./start.sh
```

---

### 8. Email goes to spam

**Likely causes:**
- Sending to yourself (same Gmail for From and To)
- Email content looks auto-generated

**Mitigations:**
- Mark the email as "Not spam" in Gmail
- Create a Gmail filter: `from:your_email subject:"News Digest"` → Never send to spam

---

### 9. Want to change your newspaper selections

**Fix:** Re-run the setup wizard:
```bash
./start.sh
```

It will ask if you want to reconfigure. Select "y" and pick new sources.

---

### 10. Want to add a newspaper that's not in the list

The available sources are defined in `newsdigest/sources.py`. To add a new one:

1. Find the newspaper's RSS feed URL (usually at `/rss` or `/feed` on their website)
2. Add a `NewsSource(...)` entry to the `AVAILABLE_SOURCES` list in `newsdigest/sources.py`
3. Re-run `./start.sh` to select it

---

## Useful Commands

```bash
# Preview the email without sending
venv/bin/python3 main.py --dry-run

# Send the digest for real
venv/bin/python3 main.py

# Force send (bypass duplicate detection)
venv/bin/python3 main.py --force

# Test just the scraper (see what articles it finds)
venv/bin/python3 -m newsdigest.scraper

# Re-run setup wizard
./start.sh

# Check Python version
venv/bin/python3 --version

# Check installed packages
venv/bin/pip list
```

---

**Previous:** [09 — Best Practices](09-best-practices.md)
