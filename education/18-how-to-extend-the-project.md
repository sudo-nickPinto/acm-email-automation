# Lesson 18 — How to Extend the Project

> **Goal:** Learn where and how to add new features to the News Digest
> system without breaking existing functionality.

---

## 1  Adding a New RSS Source

This is the most common extension.  **Three steps:**

### Step 1: Add to the registry

```python
# newsdigest/sources.py
AVAILABLE_SOURCES: list[NewsSource] = [
    # ... existing sources ...
    NewsSource(
        key="reuters_tech",
        name="Reuters — Technology",
        description="Technology news from Reuters",
        rss_url="https://www.reuters.com/technology/rss",
        max_articles=5,
    ),
]
```

### Step 2: Done.

No, really.  The scraper, emailer, setup wizard, and CLI all iterate
over `AVAILABLE_SOURCES` automatically.  The new source immediately
appears in:
- The setup wizard's source picker
- The CLI's "Change sources" menu
- The email if the user selects it

### Step 3 (optional): Write a test

```python
# tests/test_sources.py
def test_reuters_source_exists():
    from newsdigest.sources import get_source_by_key
    source = get_source_by_key("reuters_tech")
    assert source is not None
    assert source.name == "Reuters — Technology"
```

---

## 2  Supporting a Non-RSS Source

If you want to add a source that isn't RSS (e.g., an API):

1. Add a new fetching function in `scraper.py` (or a new module)
2. Return a `SourceResult` with `Article` objects
3. Integrate into `fetch_all_sources()` with a conditional

The data model (`Article`, `SourceResult`) is the contract between the
scraper and emailer.  As long as you produce these, everything downstream
works.

---

## 3  Adding a New Email Provider

Currently Gmail-only.  To add another provider:

1. Make `SMTP_SERVER` and `SMTP_PORT` configurable in `.env`
2. Update `config.py` to read them
3. Update `setup_wizard.py` to ask which provider
4. Update validation (e.g., remove `@gmail.com` requirement)

---

## 4  Adding a New OS for Scheduling

1. Add a detection case in `scheduler.py::detect_os()`
2. Write `_newos_install()`, `_newos_uninstall()`, `_newos_is_installed()`
3. Add the dispatch case to `install_schedule()`, `uninstall_schedule()`,
   `is_schedule_installed()`

The pattern is identical for every OS — the public API stays the same.

---

## 5  Modifying the Email Template

The HTML template is in `emailer.py::build_html()`.  Key constraints:

- **Inline CSS only** — email clients strip `<style>` blocks
- **No JavaScript** — email clients don't execute scripts
- **Table-based layouts** — for older email clients (optional)
- **Test in real clients** — Gmail, Apple Mail, Outlook all render differently

To test changes:
```bash
venv/bin/python3 main.py --dry-run    # Plain text preview
venv/bin/python3 main.py --force      # Send to yourself and check
```

---

## 6  Architecture Principles to Follow

| Principle | How to apply it |
|-----------|----------------|
| Single Responsibility | One module = one reason to change |
| Fail soft | Capture errors in `SourceResult.error`, don't crash |
| Type safety | Use dataclasses, not dicts |
| Comments | Explain *why*, not just *what* |
| Test offline | Mock all I/O in tests |
| Cross-platform | Test on macOS, Linux, and Windows |

---

## 7  Common Pitfalls

| Mistake | Why it's bad |
|---------|-------------|
| Adding `pip install newlib` | Users install via zip — no pip at runtime |
| Using `sys.exit()` in library code | Kills the CLI if called from menu |
| Hardcoding paths | Breaks on other machines |
| Printing credentials | Security violation |
| Skipping HTML escaping | XSS in emails |

---

## 8  Code Modification Checklist

Before submitting changes:

- [ ] Does it work on macOS, Linux, AND Windows?
- [ ] Are all network calls mocked in tests?
- [ ] Is untrusted input escaped/validated?
- [ ] Does `python -m pytest tests/ -v` pass?
- [ ] Are new features documented in education/ and docs/?
- [ ] Does `build_release.py` still produce a valid zip?

---

## 9  Key Takeaways

| Extension type | Where to change |
|----------------|----------------|
| New RSS source | `sources.py` only |
| New feed format | `scraper.py` + new fetcher |
| New email provider | `config.py` + `setup_wizard.py` |
| New OS scheduler | `scheduler.py` |
| Email styling | `emailer.py::build_html()` |
