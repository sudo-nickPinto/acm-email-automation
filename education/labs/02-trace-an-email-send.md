# Lab 02: Trace an Email Send

## Goal

Follow the control flow from `main.py` all the way to Gmail's servers,
understanding every function call in the chain.

## Steps

1. Open `main.py`.  Find the `send_email(results)` call.  This is where
   the orchestrator hands off to the emailer.

2. Open `newsdigest/emailer.py`.  Find `send_email()`.

3. Trace the SMTP sequence:
   ```python
   with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
       server.starttls()
       server.login(SMTP_EMAIL, SMTP_APP_PASSWORD)
       server.sendmail(SMTP_EMAIL, RECIPIENT_EMAIL, msg.as_string())
   ```

4. Answer these questions:
   - Where does `SMTP_SERVER` come from?  (→ `config.py`)
   - Where does `SMTP_EMAIL` come from?  (→ `.env` via `config.py`)
   - Why `starttls()` before `login()`?  (Encryption must be active
     before credentials are sent)

5. Look at `MIMEMultipart("alternative")`.  Why "alternative"?
   (The email client picks the best format — HTML if supported,
   plain text otherwise.)

6. Look at `msg.attach(MIMEText(plain, "plain"))` then
   `msg.attach(MIMEText(html, "html"))`.  Why is HTML attached second?
   (Email clients prefer the **last** alternative part.)

## Security Check

7. Open `build_html()`.  Find every place where article data is inserted
   into HTML.  Verify that each uses `_escape_html_text()` or
   `_safe_href()`.

## Questions

1. What would happen if `SMTP_APP_PASSWORD` is wrong?
2. What would happen if you used port 465 instead of 587?
3. Why does the project use an App Password instead of your Gmail password?
