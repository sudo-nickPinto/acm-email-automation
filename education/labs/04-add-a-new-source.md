# Lab 04: Add a New Source

## Goal

Add a new RSS feed source and see it automatically appear in the
setup wizard, CLI, scraper, and emailer — without touching any file
other than `sources.py`.

## Steps

1. Find an RSS feed you'd like to add.  Some options:
   - The Verge: `https://www.theverge.com/rss/index.xml`
   - Hacker News: `https://hnrss.org/frontpage`
   - Ars Technica: `https://feeds.arstechnica.com/arstechnica/index`

2. Open `newsdigest/sources.py`.

3. Add a new `NewsSource` to `AVAILABLE_SOURCES`:
   ```python
   NewsSource(
       key="verge_tech",
       name="The Verge",
       description="Technology, science, art, and culture",
       rss_url="https://www.theverge.com/rss/index.xml",
       max_articles=5,
   ),
   ```

4. Test it manually:
   ```bash
   venv/bin/python3 -c "
   from newsdigest.scraper import _fetch_single_source
   from newsdigest.sources import get_source_by_key
   source = get_source_by_key('verge_tech')
   result = _fetch_single_source(source)
   print(f'Error: {result.error}' if result.error else f'Found {len(result.articles)} articles')
   for a in result.articles[:3]:
       print(f'  - {a.title}')
   "
   ```

5. Run the test suite to ensure nothing broke:
   ```bash
   venv/bin/python3 -m pytest tests/test_sources.py -v
   ```

## Questions

1. Why does the `key` field matter?  Where is it stored?  (→ `.env`)
2. What happens if you use a key that's already taken?
3. How does `max_articles` affect the email length?
4. What would happen if the RSS feed URL returns non-XML content?
   (→ check `_fetch_single_source()` in `scraper.py`)

## Bonus

Write a test for your new source in `tests/test_sources.py`:
```python
def test_new_source_exists():
    source = get_source_by_key("verge_tech")
    assert source is not None
    assert "verge" in source.key
```
