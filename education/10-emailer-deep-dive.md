# Lesson 10 — Emailer Deep Dive

> **Goal:** Understand how `newsdigest/emailer.py` formats articles into
> both plain-text and HTML emails, and sends them via Gmail SMTP.

---

## 1  Purpose

The emailer is the **presentation and delivery layer**.  It takes
`SourceResult` objects from the scraper and produces a formatted email
with both plain-text and HTML versions.

```
SourceResult[]  →  build_plain_text()  →  MIMEText("plain")
                →  build_html()        →  MIMEText("html")
                →  MIMEMultipart("alternative")  →  Gmail SMTP
```

---

## 2  Helper Functions

### 2.1  `_time_greeting()`

```python
def _time_greeting() -> str:
    hour = datetime.now().hour
    if hour < 12:
        return "Good morning"
    elif hour < 17:
        return "Good afternoon"
    else:
        return "Good evening"
```

A small touch that makes the email feel less robotic.

### 2.2  `_edition_date()`

```python
def _edition_date() -> str:
    return datetime.now().strftime("%B %d, %Y")
```

Produces `"March 25, 2026"` — used in the subject line and email body.

### 2.3  `_escape_html_text()`

```python
def _escape_html_text(value: str) -> str:
    return html.escape(value, quote=True)
```

**Security-critical.**  Every piece of untrusted text (article titles,
descriptions) is HTML-escaped before insertion into the email.  This
prevents XSS if a malicious RSS feed includes `<script>` tags in titles.

### 2.4  `_safe_href()`

```python
def _safe_href(url: str) -> str:
    cleaned = url.strip()
    if not cleaned:
        return ""
    parsed = urlsplit(cleaned)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
        return ""
    return html.escape(cleaned, quote=True)
```

**Security-critical.**  Validates that link URLs use only `http://` or
`https://` schemes.  This blocks:
- `javascript:alert(1)` — XSS via link injection
- `data:text/html,...` — content injection
- `file:///etc/passwd` — local file access

If the URL fails validation, the link shows "Link unavailable" instead.

---

## 3  Plain-Text Builder

```python
def build_plain_text(results: list[SourceResult]) -> str:
```

Produces a clean, readable text email.  Structure:

```
Good morning,

Your news digest for March 25, 2026:

==================================================
  ACM TechNews
==================================================

  * Article Title
    Description text here...
    -> https://example.com/article

==================================================
  BBC News - Technology
==================================================

  ...

--
Sent automatically by your News Digest bot.
```

**Key decisions:**
- Uses `═` dividers for source headers — visually scannable
- Descriptions are indented 4 spaces for hierarchy
- Links prefixed with `→` for visual distinction
- Error sources show `⚠` warnings instead of crashing
- `no_new_today` sources show a message rather than being silently omitted

---

## 4  HTML Builder

```python
def build_html(results: list[SourceResult]) -> str:
```

The HTML version is what most email clients display.  Key features:

### 4.1  Inline CSS Only

```python
style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
       max-width:680px; margin:0 auto; padding:20px; color:#222; background:#fafafa;"
```

Email clients strip `<style>` blocks and external stylesheets.
**All CSS must be inline.**  The email uses a system font stack that
works across macOS (Apple), Windows (Segoe UI), and Linux (Roboto).

### 4.2  Color-Cycling Headers

```python
colors = ["#0066cc", "#d35400", "#27ae60", "#8e44ad"]
color = colors[i % len(colors)]
```

Each source section gets a different header color (blue, orange, green,
purple).  The modulo operator (`%`) cycles if there are more than 4 sources.

### 4.3  Article Cards

Each article is a styled `<div>` with:
- Title as `<h3>` in dark color
- Description in gray (`#555`)
- "Read full article →" link in the source's header color
- Bottom border separating cards

### 4.4  Error Display

Failed sources get a yellow warning banner:
```html
<div style="background:#fff3cd;border-left:4px solid #ffc107;">
  <strong>⚠ BBC News</strong> — Connection failed
</div>
```

---

## 5  Sending the Email

```python
def send_email(results: list[SourceResult]) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Your News Digest — {_edition_date()}"
    msg["From"] = SMTP_EMAIL
    msg["To"] = RECIPIENT_EMAIL

    plain = build_plain_text(results)
    html = build_html(results)

    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_APP_PASSWORD)
        server.sendmail(SMTP_EMAIL, RECIPIENT_EMAIL, msg.as_string())
```

### 5.1  MIME Structure

`MIMEMultipart("alternative")` tells the email client: "here are two
versions of the same content — pick the best one."  Email clients prefer
the **last** attachment, so HTML goes second.

### 5.2  SMTP Connection

```
Client                        Gmail
  |  ── TCP connect ──────→    :587
  |  ← 220 Ready ─────────    |
  |  ── STARTTLS ─────────→   |
  |  ← 220 TLS OK ────────    |
  |  ── AUTH LOGIN ────────→   |   (credentials encrypted)
  |  ← 235 Authenticated ─    |
  |  ── MAIL FROM / DATA ──→  |
  |  ← 250 OK ────────────    |
  |  ── QUIT ──────────────→  |
```

**Why port 587 + STARTTLS?**
- Port 465 (SMTPS) wraps the entire connection in TLS from the start
- Port 587 (Submission) starts unencrypted, then upgrades via STARTTLS
- Gmail supports both, but 587 is the IETF-recommended submission port

**Why App Passwords?**  Gmail blocks regular passwords for
"less secure apps."  App Passwords bypass this while maintaining 2FA
security on the account.

---

## 6  Security Summary

| Threat | Mitigation |
|--------|-----------|
| XSS in article titles | `_escape_html_text()` using `html.escape()` |
| Malicious URLs in links | `_safe_href()` allows only `http`/`https` |
| Credential interception | STARTTLS encrypts the SMTP session |
| Password exposure | App Password, not account password |

---

## 7  Key Takeaways

| Concept | Implementation |
|---------|---------------|
| Multipart email | `MIMEMultipart("alternative")` with plain + HTML |
| Security first | HTML escaping + URL scheme validation |
| Inline CSS | Required by email clients — no external stylesheets |
| Graceful degradation | Errors shown as warnings, not crashes |
