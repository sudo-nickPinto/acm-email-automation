# Runtime Flow Diagram

## Normal Send

```
main.py
  │
  ├─ Parse flags: --dry-run, --force
  │
  ├─ Validate: SELECTED_SOURCES not empty
  │     └─ Empty? → exit 1 ("Run ./start.sh to set up")
  │
  ├─ fetch_all_sources()                    ← scraper.py
  │     ├─ For each key in SELECTED_SOURCES:
  │     │     ├─ get_source_by_key(key)     ← sources.py
  │     │     ├─ HTTP GET source.rss_url    ← requests
  │     │     ├─ Parse XML (ElementTree)
  │     │     ├─ Extract <item> elements
  │     │     ├─ Clean HTML descriptions
  │     │     └─ Return SourceResult(articles=[...])
  │     │           or SourceResult(error="...")
  │     └─ Return list[SourceResult]
  │
  ├─ Filter to today's articles
  │     ├─ _is_published_today() for each article
  │     ├─ Set no_new_today=True if source had articles but none fresh
  │     └─ Replace articles list with filtered version
  │
  ├─ Count: total articles, errors, stale sources
  │     └─ All zero? → exit 1
  │
  ├─ _results_hash()                        ← SHA-256 of date + titles
  │     └─ _already_sent()? → exit 0 (unless --force)
  │
  ├─ --dry-run?
  │     ├─ Yes → print build_plain_text() → return (no state save)
  │     └─ No ↓
  │
  ├─ send_email(results)                    ← emailer.py
  │     ├─ build_plain_text(results)
  │     ├─ build_html(results)
  │     ├─ MIMEMultipart("alternative")
  │     ├─ SMTP connect → STARTTLS → login → send
  │     └─ Print "Email sent to ..."
  │
  └─ _save_state(current_hash)              ← write .last_sent
```

## Data Flow

```
RSS XML bytes
  → ElementTree parsing
    → Article dataclasses
      → SourceResult containers
        → Plain text string + HTML string
          → MIMEMultipart email
            → Gmail SMTP
              → Recipient inbox
```
