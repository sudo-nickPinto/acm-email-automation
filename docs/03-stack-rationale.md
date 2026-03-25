# 03 — Stack Rationale

## Why These Tools?

Every technology choice in this project was made for a reason. This document explains what we picked, what the alternatives were, and why we went this direction.

---

## Language: Python 3

### Why Python?

- **Best-in-class for scripting** — Python is the standard for "glue code" that connects APIs, parses data, and automates tasks
- **Rich standard library** — XML parsing (`xml.etree`), email composition (`email.mime`), SMTP (`smtplib`), hashing (`hashlib`), and file I/O (`pathlib`) are all built in
- **Low ceremony** — no compilation step, no type system overhead for a small project. You write, you run
- **Widely available** — Python 3 comes pre-installed on macOS and most Linux distributions

### Why not...

| Alternative | Reason we didn't use it |
|-------------|------------------------|
| Node.js | Could work, but Python's stdlib has SMTP and XML built in. Node would require npm packages for everything |
| Bash | Great for simple tasks, but XML parsing in bash is painful. The setup wizard's interactive prompts and validation would be ugly |
| Go | Compiled binary would be nice for distribution, but overkill for a small project |
| Rust | Way too heavy for this use case |

---

## HTTP Client: `requests`

### What it does

`requests` makes HTTP calls (GET, POST, etc.). We use it to fetch RSS feed XML from each newspaper's server.

### Why not `urllib` (built-in)?

Python has `urllib` in the standard library, but compare:

```python
# urllib (built-in) — verbose, confusing API
import urllib.request
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=30) as response:
    data = response.read()

# requests (pip install) — clean, obvious
import requests
response = requests.get(url, timeout=30)
data = response.content
```

`requests` is the de-facto standard for HTTP in Python. Its API is so much better that it's worth the one extra dependency.

### Key features we use

- `requests.get(url, timeout=30)` — makes the GET request with a timeout
- `response.raise_for_status()` — raises an exception if the server returns 4xx/5xx
- `response.content` — the raw bytes of the response body

---

## XML Parsing: `xml.etree.ElementTree` (built-in)

### What it does

Parses XML documents into a tree of `Element` objects that you can navigate with `.find()`, `.findall()`, and `.findtext()`.

### Why not BeautifulSoup?

BeautifulSoup shines when parsing messy, broken HTML (like real web pages). RSS feeds are valid XML, so `ElementTree` is the right tool — it's faster, built-in, and designed specifically for XML.

### RSS feed structure

All four of our sources use standard RSS 2.0:

```xml
<rss>
  <channel>
    <title>BBC News - Technology</title>
    <item>
      <title>AI Helps Detect Cancer Earlier</title>
      <link>https://...</link>
      <description>Researchers have developed...</description>
      <pubDate>Mon, 24 Mar 2026 08:00:00 GMT</pubDate>
    </item>
    <item>...</item>
  </channel>
</rss>
```

We call `root.find("channel")` to get the channel, then `channel.findall("item")` to iterate over articles.

---

## Email: `smtplib` + `email.mime` (built-in)

### What it does

- `email.mime` constructs properly formatted email messages (headers, body, MIME types)
- `smtplib` sends them over the SMTP protocol

### Why not a third-party email service?

| Option | Pros | Cons |
|--------|------|------|
| Gmail SMTP (what we use) | Free, no API key signup, works with any Gmail account | Requires App Password, 500 emails/day limit |
| SendGrid | Professional, high deliverability | Requires account signup, API key management |
| Mailgun | Great API | Same overhead as SendGrid |
| Amazon SES | Cheap at scale | AWS account, IAM roles, overkill |

For a personal project sending a few emails per week, Gmail SMTP is the simplest path. No external API keys, no webhook configuration, no billing. Just your Gmail address and an App Password.

---

## Environment Variables: `python-dotenv`

### What it does

Reads `KEY=VALUE` pairs from a `.env` file and loads them into the process environment so `os.getenv()` can find them.

### Why not hard-code credentials?

**Never hard-code secrets.** If you commit a password to git:

1. It's in the git history forever (even if you delete the file later)
2. Anyone who clones the repo has your credentials
3. GitHub will flag it and might revoke the credential automatically

The `.env` file is listed in `.gitignore`, so git never sees it. The `.env.example` file acts as a template showing **what** variables are needed without **any** actual values.

### Why not system environment variables?

You could set `export SMTP_PASSWORD=...` in your shell profile, but:

1. Non-technical users don't know what shell profiles are
2. The setup wizard writes `.env` automatically — no manual editing
3. The `.env` file keeps all project config in one place

---

## Bootstrap: Bash (`start.sh`)

### Why a shell script?

Python can't install itself. We need something that runs _before_ Python exists on the system. Bash is available on macOS and Linux natively, and on Windows through Git Bash or WSL. For native Windows users who have only PowerShell, `install.ps1` handles the bootstrap directly in PowerShell.

### Why not just tell users to install Python?

Our target audience is non-technical friends. "Install Python 3.10+" is a surprisingly complex instruction for someone who has never used a package manager. `start.sh` detects whether Python is installed, and if not, provides OS-specific step-by-step instructions (with Homebrew auto-detection on macOS, apt/dnf/pacman detection on Linux, and python.org/winget guidance on Windows).

---

## Setup Wizard: Python (`setup_wizard.py`)

### Why a separate wizard instead of command-line flags?

1. **Discoverability** — a numbered list of newspapers is easier to understand than `--source=acm_technews --source=bbc_tech`
2. **Validation** — the wizard checks that the Gmail address ends with `@gmail.com` and the App Password is exactly 16 letters
3. **Guidance** — the wizard explains _what_ an App Password is and _how_ to get one, with numbered steps
4. **Portability** — the wizard writes the `.env` file automatically, so users never touch a config file

---

**Previous:** [02 — System Design](02-system-design.md)
**Next:** [04 — Config and Environment](04-config-and-environment.md)
