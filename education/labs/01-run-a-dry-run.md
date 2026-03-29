# Lab 01: Run a Dry Run

## Goal

See the digest output without sending an email.  Trace which parts of
the output come from the scraper and which come from the emailer.

## Prerequisites

- Project installed with at least one source selected
- `.env` file configured with valid source selection

## Steps

1. Open your terminal in the project directory.

2. Run the dry-run command:
   ```bash
   # macOS/Linux
   venv/bin/python3 main.py --dry-run

   # Windows
   venv\Scripts\python.exe main.py --dry-run
   ```

3. Observe the output.  You'll see two sections:
   - **Fetch output** — lines like `Fetching BBC News...` and `✔ 5 articles`
   - **Plain-text preview** — the formatted email body

4. Open `newsdigest/scraper.py` and find the `print()` calls in
   `fetch_all_sources()`.  These produce the fetch output.

5. Open `newsdigest/emailer.py` and find `build_plain_text()`.  This
   produces the preview body.

## Questions

1. Which sources are included in your output?  Match them to your
   `SELECTED_SOURCES` in `.env`.

2. Do any sources show "No new articles published today"?  Why might
   this happen?  (Hint: check `_is_published_today()` in `scraper.py`)

3. Does the dry run create or modify `.last_sent`?  Why not?
   (Hint: check `main.py` — what happens after the dry-run print?)

## Bonus

Run `--dry-run` twice in a row.  Does the second run show "Already
sent"?  Why or why not?
