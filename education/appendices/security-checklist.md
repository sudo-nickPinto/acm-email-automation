# Security Checklist

Use this checklist when reviewing changes or auditing the installation.

## Credentials

- [ ] `.env` file has `chmod 600` on POSIX systems
- [ ] `.env` is listed in `.gitignore`
- [ ] Passwords are entered via `getpass` (hidden input)
- [ ] No credentials are printed to stdout or logs
- [ ] Gmail App Password is used (not account password)
- [ ] 2FA is enabled on the Gmail account

## Untrusted Input (RSS Feeds)

- [ ] Article titles are HTML-escaped before email insertion (`_escape_html_text()`)
- [ ] Article descriptions are HTML-escaped
- [ ] URLs are validated for `http`/`https` scheme only (`_safe_href()`)
- [ ] HTML tags are stripped from RSS content (`_clean_html()`)
- [ ] No `eval()`, `exec()`, or dynamic code execution on feed content

## Installer Security

- [ ] Downloads use HTTPS with TLS verification
- [ ] `SHA256SUMS.txt` is downloaded and verified against the zip
- [ ] Checksum mismatch aborts installation immediately
- [ ] `build_release.py` enforces clean worktree (no uncommitted changes)
- [ ] Installer scripts use env variable overrides for testing (not hardcoded paths)

## Network

- [ ] HTTP requests have a timeout (`REQUEST_TIMEOUT = 30`)
- [ ] SMTP uses STARTTLS encryption
- [ ] Connection errors are caught and reported (not swallowed)

## Scheduling

- [ ] All scheduling is user-level (no root/sudo/admin)
- [ ] Scheduled commands use absolute venv Python path (not PATH-dependent)
- [ ] Shell paths in crontab are quoted with `shlex.quote()`
- [ ] LaunchAgent plist uses absolute paths

## Development

- [ ] Tests mock all network calls (run fully offline)
- [ ] CI runs on all three platforms (macOS, Linux, Windows)
- [ ] Release builds exclude dev files (tests, scripts, education, .github)
