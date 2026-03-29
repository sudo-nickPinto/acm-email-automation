# Lesson 14 — Security Model and Threats

> **Goal:** Understand every security decision in the project — what
> threats exist, how they're mitigated, and why each defence was chosen.

---

## 1  Threat Model

This project handles **email credentials** and **untrusted RSS content**.
The attack surface is:

| Asset | Threat | Impact |
|-------|--------|--------|
| Gmail App Password | Exposure via .env or logs | Attacker sends email as you |
| Email address | Exposure | Spam, social engineering |
| RSS content | XSS, injection | Malicious content in email |
| Installer downloads | MITM, tampering | Code execution on user machine |
| Scheduled tasks | Hijacking | Persistent malware |

---

## 2  Credential Protection

### 2.1  `.env` File Permissions

```python
# setup_wizard.py
def _protect_secret_file(path: Path) -> None:
    if os.name == "nt":
        return
    try:
        path.chmod(0o600)
    except OSError:
        pass
```

`chmod 600` = owner can read/write, nobody else can.  On shared systems,
this prevents other users from reading your email password.

### 2.2  Hidden Password Entry

```python
# cli.py
password = getpass.getpass("  New App Password (or 'cancel'): ")
```

`getpass` disables terminal echo so the password isn't visible on screen.

### 2.3  App Password vs Account Password

Gmail App Passwords are:
- **Scoped** — they can only access SMTP, not your full Google account
- **Revocable** — you can delete one without changing your real password
- **Require 2FA** — your account must have 2FA enabled first

The wizard explains this tradeoff and links directly to the App Password
creation page.

### 2.4  `.gitignore` Protection

```
.env
.last_sent
logs/
```

These entries prevent accidental credential commits.

---

## 3  Content Security (Untrusted RSS)

### 3.1  HTML Escaping

```python
# emailer.py
def _escape_html_text(value: str) -> str:
    return html.escape(value, quote=True)
```

Every article title and description passes through `html.escape()` before
being placed in HTML.  This converts:
- `<script>` → `&lt;script&gt;`
- `"onclick=..."` → `&quot;onclick=...&quot;`

### 3.2  URL Scheme Validation

```python
# emailer.py
def _safe_href(url: str) -> str:
    parsed = urlsplit(cleaned)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
        return ""
    return html.escape(cleaned, quote=True)
```

This blocks `javascript:`, `data:`, and `file:` URLs.  Only `http` and
`https` links appear in the email.

### 3.3  HTML Tag Stripping

```python
# scraper.py
def _clean_html(raw_html: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
```

RSS descriptions can contain arbitrary HTML.  We strip all tags and decode
entities before storing the text.

---

## 4  Installer Security

### 4.1  SHA-256 Integrity Verification

Both `install.sh` and `install.ps1` verify the downloaded zip's checksum:

**Bash:**
```bash
EXPECTED=$(grep "news-digest.zip" "$SHA_FILE" | awk '{print $1}')
ACTUAL=$(shasum -a 256 "$ZIP_FILE" | awk '{print $1}')
if [[ "$ACTUAL" != "$EXPECTED" ]]; then
    echo "CHECKSUM MISMATCH"; exit 1
fi
```

**PowerShell:**
```powershell
$expected = (Get-Content $shaFile | Select-String "news-digest.zip") -split '\s+' | Select-Object -First 1
$actual = (Get-FileHash $zipFile -Algorithm SHA256).Hash
if ($actual -ne $expected) {
    Write-Host "CHECKSUM MISMATCH"; exit 1
}
```

This detects:
- Corrupted downloads
- MITM attacks (if the attacker can't also modify `SHA256SUMS.txt`)

### 4.2  HTTPS-Only Downloads

All downloads use HTTPS.  `curl -fsSL` in bash and `Invoke-WebRequest`
in PowerShell both verify TLS certificates by default.

### 4.3  Clean Worktree Enforcement

```python
# build_release.py
def ensure_clean_worktree() -> None:
    result = subprocess.run(["git", "status", "--porcelain", ...])
    if result.stdout.strip():
        raise SystemExit("Refusing to build from a dirty worktree.")
```

Prevents accidental inclusion of debug code, credentials, or unfinished
changes in release builds.

---

## 5  SMTP Security

### 5.1  STARTTLS

```python
with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
    server.starttls()
    server.login(SMTP_EMAIL, SMTP_APP_PASSWORD)
```

The connection starts unencrypted on port 587, then upgrades to TLS via
`STARTTLS`.  After the upgrade, all data (including credentials) is
encrypted.

### 5.2  No Credential Logging

The project never prints or logs credentials.  Password entry uses
`getpass`, and the `.env` file is excluded from logs and git.

---

## 6  Scheduling Security

- **User-level only** — no root/sudo privileges needed
- macOS LaunchAgent lives in user's `~/Library/LaunchAgents/`
- Linux cron uses the user's personal crontab
- Windows Task Scheduler creates under the user's account
- The schedule runs a specific venv Python, not a PATH-dependent command

---

## 7  What's NOT Covered

| Gap | Reason |
|-----|--------|
| `.env` encryption at rest | Adds complexity; `chmod 600` is standard practice |
| Certificate pinning for RSS | Feeds are public; TLS is sufficient |
| Rate limiting | Only runs once daily; no abuse vector |
| Multi-user access control | Single-user tool by design |

---

## 8  Key Takeaways

| Principle | How it's applied |
|-----------|-----------------|
| Defence in depth | Multiple layers: permissions, escaping, validation |
| Least privilege | User-level scheduling, App Passwords |
| Fail secure | Invalid URLs → "Link unavailable" (not crash) |
| Verify integrity | SHA-256 checksums on installer downloads |
| Don't log secrets | `getpass`, `.gitignore`, no credential output |
