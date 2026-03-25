# 06 — Emailer Deep Dive

## What This Module Does

`emailer.py` takes a list of `SourceResult` objects (from the scraper) and:
1. Formats them into a multi-section email with both plain-text and HTML versions
2. Sends that email through Gmail's SMTP server

Think of it as the "newsletter layout editor" that also handles delivery.

## Big Picture Flow

```
list[SourceResult]
     │
     ├──► build_plain_text()  ──►  plain text string
     │                                    │
     ├──► build_html()        ──►  HTML string
     │                                    │
     ▼                                    ▼
send_email()                    MIMEMultipart message
     │                          (plain + HTML attached)
     │
     ├── smtplib.SMTP() → connect to smtp.gmail.com:587
     ├── .starttls()     → upgrade to encrypted
     ├── .login()        → authenticate
     ├── .sendmail()     → deliver
     └── (context manager closes connection)
```

## Key Functions

### Helper Functions

```python
def _time_greeting() -> str:
    hour = datetime.now().hour
    if hour < 12:   return "Good morning"
    elif hour < 17: return "Good afternoon"
    else:           return "Good evening"
```

A small personalization touch. The leading underscore is a Python convention meaning "internal/private function."

```python
def _edition_date() -> str:
    return datetime.now().strftime("%B %d, %Y")
```

Produces `"March 25, 2026"`. `%B` = full month, `%d` = day, `%Y` = year.

### `build_plain_text(results)`

Constructs the plain-text version of the email. This is what `--dry-run` prints to the terminal. Structure:

```
Good morning,

Your news digest for March 25, 2026:

==================================================
  ACM TechNews
==================================================

  • AI Helps Detect Cancer Earlier
    Researchers have developed a new AI system...
    → https://example.com/article1

  • Quantum Computing Reaches New Milestone
    A team at MIT has demonstrated...
    → https://example.com/article2

==================================================
  BBC News — Technology
==================================================

  • Europe Approves New Data Privacy Rules
    The European Parliament voted today...
    → https://bbc.co.uk/article1

—
Sent automatically by your News Digest bot.
Manage your sources by re-running: ./start.sh
```

Each source gets its own section with a separator line. Sources that failed show a warning instead of articles. Sources with zero articles are skipped entirely.

**Why build a list of lines instead of concatenating strings?**

```python
# Bad: O(n²) — creates a new string object every iteration
result = ""
for item in items:
    result += item + "\n"

# Good: O(n) — builds a list then joins once
lines = []
for item in items:
    lines.append(item)
result = "\n".join(lines)
```

Strings are immutable in Python. Concatenation creates a new object each time. Appending to a list and joining once is the standard pattern.

### `build_html(results)`

Produces the HTML version displayed by Gmail, Outlook, and Apple Mail. Key design decisions:

**Inline styles everywhere:**

```html
<!-- This WON'T work in email clients: -->
<style>h3 { color: #1a1a2e; }</style>

<!-- This WILL work: -->
<h3 style="color:#1a1a2e;">Title</h3>
```

Email clients strip `<style>` blocks for security. The only reliable way to style HTML email is with inline `style` attributes.

**Source-specific colored headers:**

Each newspaper section gets a colored header bar:

| Source # | Color | Hex |
|----------|-------|-----|
| 1st | Blue | `#0066cc` |
| 2nd | Orange | `#d35400` |
| 3rd | Green | `#27ae60` |
| 4th | Purple | `#8e44ad` |

Colors cycle if there are more than 4 sources.

**Article cards:**

Each article appears as a mini-card with:
- Bold title
- Gray description text (newlines converted to `<br>`)
- Colored "Read full article →" link
- Subtle bottom border separating articles

**Error handling in HTML:**

Failed sources get a yellow warning banner:

```html
<div style="background:#fff3cd;border-left:4px solid #ffc107;">
  ⚠ BBC News — Technology — Connection failed
</div>
```

**System font stack:**

```html
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
```

This uses the operating system's native font — San Francisco on Apple, Segoe UI on Windows, Roboto on Android. Clean and familiar on every device.

### `send_email(results)`

The top-level function called by `main.py`:

1. Creates a `MIMEMultipart("alternative")` container
2. Sets Subject to `"Your News Digest — March 25, 2026"`
3. Builds both plain-text and HTML bodies
4. Attaches plain-text first, HTML second (email clients prefer the last part)
5. Opens a TLS connection to Gmail
6. Authenticates and sends

```python
with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
    server.starttls()
    server.login(SMTP_EMAIL, SMTP_APP_PASSWORD)
    server.sendmail(SMTP_EMAIL, RECIPIENT_EMAIL, msg.as_string())
```

The `with` statement (context manager) ensures the SMTP connection is closed even if an exception occurs during sending.

## SMTP Protocol Summary

```
Client                          Server (smtp.gmail.com:587)
  │                                │
  ├── connect ──────────────────► │  (TCP handshake)
  ├── STARTTLS ─────────────────► │  (upgrade to encrypted)
  ├── AUTH LOGIN ───────────────► │  (email + app password)
  ├── MAIL FROM: <sender> ─────► │
  ├── RCPT TO: <recipient> ────► │
  ├── DATA ─────────────────────► │  (email headers + body)
  ├── QUIT ─────────────────────► │
  │                                │
```

Python's `smtplib` handles all of this. We only call `starttls()`, `login()`, and `sendmail()`.

---

**Previous:** [05 — Scraper Deep Dive](05-scraper-deep-dive.md)
**Next:** [07 — Main Orchestrator](07-main-orchestrator.md)
