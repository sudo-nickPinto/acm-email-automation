# Lesson 15 — Testing Strategy

> **Goal:** Understand how the 155+ test suite is structured, what
> patterns it uses, and why every test runs fully offline.

---

## 1  Test Suite Overview

```
tests/
  conftest.py           → Shared fixtures and sample data
  test_build_release.py → Release packaging (134 lines)
  test_cli.py           → Interactive CLI menu (405 lines)
  test_config.py        → Configuration loading (86 lines)
  test_emailer.py       → Email formatting (296 lines)
  test_install_ps1.py   → Windows installer (135 lines)
  test_install_sh.py    → macOS/Linux installer (136 lines)
  test_main.py          → Orchestrator/dedup (235 lines)
  test_paths.py         → Path helpers (30 lines)
  test_scheduler.py     → Scheduling (180 lines)
  test_scraper.py       → RSS parsing (282 lines)
  test_sources.py       → Source registry (75 lines)
```

Total: **~2100 lines** of test code for ~2400 lines of production code.
Nearly 1:1 ratio — comprehensive coverage.

---

## 2  Running Tests

```bash
# With venv activated
python -m pytest tests/ -v

# Specific file
python -m pytest tests/test_scraper.py -v

# Specific test
python -m pytest tests/test_scraper.py::TestCleanHtml::test_strips_tags -v
```

---

## 3  Shared Fixtures (`conftest.py`)

```python
@pytest.fixture
def sample_source() -> NewsSource:
    return NewsSource(
        key="test_source",
        name="Test News",
        description="A fake source for testing",
        rss_url="https://example.com/rss.xml",
        max_articles=3,
    )

@pytest.fixture
def sample_article() -> Article:
    return Article(
        title="Test Article Title",
        description="This is a test description.",
        link="https://example.com/article/1",
        source_name="Test News",
        pub_date="Mon, 01 Jan 2026 08:00:00 GMT",
    )
```

**Why fixtures?**  They create fresh objects for each test, preventing
state leakage between tests.  If one test mutates an article, the next
test gets a clean copy.

The conftest also defines **sample RSS XML** — complete XML strings that
simulate real RSS feeds without needing network access.

---

## 4  Mocking Patterns

### 4.1  Network Mocking

```python
@patch("newsdigest.scraper.requests.get")
def test_success_parses_articles(self, mock_get):
    mock_resp = MagicMock()
    mock_resp.content = SAMPLE_RSS_XML.encode()
    mock_resp.raise_for_status = MagicMock()
    mock_get.return_value = mock_resp

    result = _fetch_single_source(source)
    assert len(result.articles) == 3
```

**All network calls are mocked.**  `@patch` replaces `requests.get` with
a `MagicMock` that returns canned responses.  This means:
- Tests run offline
- Tests run fast (no HTTP latency)
- Tests are deterministic (same input → same output)

### 4.2  Environment Mocking

```python
@patch.dict(os.environ, {"SMTP_EMAIL": "test@gmail.com", ...})
def test_config_loads():
    importlib.reload(config)
    assert config.SMTP_EMAIL == "test@gmail.com"
```

Config tests use `@patch.dict(os.environ, ...)` to inject environment
variables without touching the real `.env` file.

### 4.3  Filesystem Mocking

```python
@patch("pathlib.Path.exists", return_value=True)
@patch("pathlib.Path.read_text", return_value="abc123hash")
def test_already_sent(mock_read, mock_exists):
    assert _already_sent("abc123hash") is True
```

State file operations are mocked so tests don't create real files.

### 4.4  Subprocess Mocking

```python
@patch("subprocess.run")
def test_macos_install(self, mock_run):
    mock_run.return_value = MagicMock(returncode=0)
    _macos_install(8, 0)
    mock_run.assert_called()
```

Scheduler tests mock `subprocess.run` to avoid actually installing
LaunchAgents or crontab entries on the test machine.

---

## 5  Test Organization

### 5.1  Class-Based Grouping

```python
class TestCleanHtml:
    def test_strips_tags(self): ...
    def test_removes_img_tags(self): ...
    def test_decodes_entities(self): ...
```

Related tests are grouped in classes.  This provides:
- Visual organization in test output
- Shared setup if needed (via `setup_method`)
- Easy filtering (`pytest -k TestCleanHtml`)

### 5.2  Naming Convention

```
test_<function>_<scenario>
```

Examples:
- `test_success_parses_articles` — happy path
- `test_timeout_returns_error` — specific error condition
- `test_max_articles_limit` — boundary condition

---

## 6  Platform-Specific Tests

### 6.1  Unix-Only Tests

```python
# test_install_sh.py
pytestmark = pytest.mark.skipif(
    sys.platform == "win32",
    reason="Shell-installer tests require bash"
)
```

The `pytestmark` module-level skip ensures Windows CI doesn't try to
parse bash scripts.

### 6.2  Windows-Specific Tests

```python
# test_install_ps1.py
if sys.platform != "win32":
    # Tests for symlink creation use os.symlink which needs different
    # paths on Windows vs POSIX
```

PowerShell installer tests include Windows-specific path handling.

---

## 7  What Each Test File Covers

| File | Key scenarios tested |
|------|---------------------|
| `test_scraper.py` | HTML cleaning, XML parsing, timeout handling, HTTP errors, date parsing |
| `test_emailer.py` | Plain text format, HTML escaping, URL validation, SMTP mocking, error display |
| `test_main.py` | Dedup hash, state file ops, dry-run behavior, force flag, article filtering |
| `test_cli.py` | Menu dispatch, env read/write, source selection, password validation, uninstall |
| `test_scheduler.py` | LaunchAgent creation, cron tag parsing, schtasks calls, OS detection |
| `test_config.py` | Env var parsing, default values, empty configs |
| `test_sources.py` | Source lookup, key uniqueness, dataclass fields |
| `test_paths.py` | Cross-platform Python paths |
| `test_install_sh.py` | Bash script structure, checksum commands |
| `test_install_ps1.py` | PowerShell script structure, checksum logic |
| `test_build_release.py` | File exclusion, zip structure, checksum generation, clean worktree |

---

## 8  CI Integration

The GitHub Actions workflow runs the full suite on:

| Platform | Python Versions |
|----------|----------------|
| ubuntu-latest | 3.10, 3.12, 3.13 |
| macos-latest | 3.10, 3.12, 3.13 |
| windows-latest | 3.10, 3.12, 3.13 |

Plus two smoke tests:
- **Windows installer** — builds a release, serves it locally, runs the
  real `install.ps1` against it
- **Windows launcher** — creates a venv in-place and runs
  `news-digest.ps1 help`

---

## 9  Key Takeaways

| Principle | Implementation |
|-----------|---------------|
| 100% offline | All network calls mocked |
| Deterministic | No time/date dependencies in assertions |
| Fast | No I/O, no network — full suite in seconds |
| Comprehensive | ~1:1 test-to-production code ratio |
| Cross-platform | Platform-specific skips, CI matrix |
