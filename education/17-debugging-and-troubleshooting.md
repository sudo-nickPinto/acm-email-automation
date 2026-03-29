# Lesson 17 — Debugging and Troubleshooting

> **Goal:** Learn how to diagnose and fix common issues with the
> News Digest system.

---

## 1  Diagnostic Commands

```bash
# Check current configuration
news-digest              # Option 8: View Status

# Preview without sending
venv/bin/python3 main.py --dry-run

# Force-send (bypass dedup)
venv/bin/python3 main.py --force

# Run a single module
venv/bin/python3 -c "from newsdigest.scraper import _fetch_single_source; ..."

# Run tests
venv/bin/python3 -m pytest tests/ -v
```

---

## 2  Common Issues

### 2.1  "No news sources configured"

**Cause:** `.env` file is missing or `SELECTED_SOURCES` is empty.

**Fix:**
```bash
./start.sh    # Re-run the setup wizard
```

### 2.2  "Already sent this digest"

**Cause:** The dedup check found a matching hash in `.last_sent`.

**Fix:**
```bash
venv/bin/python3 main.py --force    # Bypass dedup
# or
rm .last_sent                        # Clear state
```

### 2.3  SMTP Authentication Failed

**Causes:**
- Wrong App Password
- 2FA not enabled on Gmail account
- Regular password used instead of App Password

**Fix:**
1. Enable 2FA: https://myaccount.google.com/security
2. Generate App Password: https://myaccount.google.com/apppasswords
3. Update via `news-digest` → Option 6

### 2.4  "Connection failed — check your internet"

**Cause:** Network issue or RSS feed URL is down.

**Diagnosis:**
```bash
curl -I https://feeds.bbci.co.uk/news/technology/rss.xml
```

The scraper handles this gracefully per-source — other sources still work.

### 2.5  Schedule Not Firing

**macOS:**
```bash
# Check if loaded
launchctl list | grep newsdigest

# Check plist
cat ~/Library/LaunchAgents/com.newsdigest.daily.plist

# Check logs
cat logs/stdout.log
cat logs/stderr.log
```

**Linux:**
```bash
crontab -l | grep newsdigest
```

**Windows:**
```powershell
schtasks /Query /TN "com.newsdigest.daily"
```

### 2.6  "No new articles published today"

This is normal.  Some sources (like ACM TechNews) only publish on
specific days (Mon/Wed/Fri).  The system correctly filters to today-only
articles.

---

## 3  Log Files

Scheduled runs write to:
- `logs/stdout.log` — normal output
- `logs/stderr.log` — errors

These are the **only visibility** into scheduled runs since they have
no terminal.

---

## 4  State Files

| File | Purpose | Safe to delete? |
|------|---------|-----------------|
| `.env` | Credentials and settings | No — need to re-run wizard |
| `.last_sent` | Dedup hash | Yes — next run will send |
| `logs/` | Schedule output | Yes — just diagnostic data |

---

## 5  Environment Variables for Debugging

```bash
# Skip clean worktree check in builds
export NEWSDIGEST_ALLOW_DIRTY=1

# Override installer URLs (for testing)
export NEWSDIGEST_RELEASE_BASE_URL="http://localhost:8199"
export NEWSDIGEST_INSTALL_DIR="/tmp/test-install"
export NEWSDIGEST_SKIP_LAUNCH=1
```

---

## 6  Key Takeaways

| Situation | Tool |
|-----------|------|
| Nothing sending | Check `.env`, check `--dry-run` |
| Duplicate blocked | Use `--force` or delete `.last_sent` |
| SMTP errors | Verify App Password + 2FA |
| Schedule silent | Check `logs/` directory |
| Source down | Other sources still work (fail-soft) |
