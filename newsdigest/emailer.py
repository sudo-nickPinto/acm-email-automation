# =============================================================================
# emailer.py — Multi-Source Digest Email Formatter and Sender (v2)
# =============================================================================
#
# Takes articles from multiple newspaper sources and formats them into a
# single, clean digest email delivered via Gmail SMTP.
#
# What changed from v1:
# ---------------------
# v1 formatted a single-source ACM TechNews email.  v2 organizes articles
# by source — each newspaper gets its own section with a header, making it
# easy to scan.
#
# Email format:
# -------------
# We send a "multipart/alternative" email with both plain-text and HTML.
# The HTML version has styled sections per source.  The plain-text version
# is readable in terminal email clients and used by --dry-run.
#
# Dependencies:
#   smtplib, datetime, email.mime — all stdlib
#   config — local configuration module
#   scraper — for the Article and SourceResult types
# =============================================================================

"""
Email sender module — formats and sends the multi-source news digest.
"""

import html
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from urllib.parse import urlsplit

from newsdigest.config import RECIPIENT_EMAIL, SMTP_APP_PASSWORD, SMTP_EMAIL, SMTP_PORT, SMTP_SERVER
from newsdigest.scraper import Article, SourceResult


def _time_greeting() -> str:
    """
    Return a time-appropriate greeting based on the current hour.
    """
    hour = datetime.now().hour
    if hour < 12:
        return "Good morning"
    elif hour < 17:
        return "Good afternoon"
    else:
        return "Good evening"


def _edition_date() -> str:
    """
    Return today's date in a human-friendly format like "March 25, 2026".
    """
    return datetime.now().strftime("%B %d, %Y")


def _escape_html_text(value: str) -> str:
    """Escape untrusted text before placing it into the HTML email."""
    return html.escape(value, quote=True)


def _safe_href(url: str) -> str:
    """
    Allow only ordinary web links in HTML output.
    """
    cleaned = url.strip()
    if not cleaned:
        return ""

    parsed = urlsplit(cleaned)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
        return ""

    return html.escape(cleaned, quote=True)


def build_plain_text(results: list[SourceResult]) -> str:
    """
    Build the plain-text version of the multi-source digest email.

    Structure:
      1. Greeting + date
      2. For each source:
         - Source header
         - Article titles + descriptions + links
      3. Footer
    """
    greeting = _time_greeting()
    date = _edition_date()

    lines = [
        f"{greeting},",
        "",
        f"Your news digest for {date}:",
        "",
    ]

    for result in results:
        if result.error:
            lines.append(f"{'=' * 50}")
            lines.append(f"⚠ {result.source.name} — {result.error}")
            lines.append(f"{'=' * 50}")
            lines.append("")
            continue

        if result.no_new_today:
            lines.append(f"{'=' * 50}")
            lines.append(f"  {result.source.name}")
            lines.append(f"{'=' * 50}")
            lines.append("")
            lines.append("  No new articles published today.")
            lines.append("")
            continue

        if not result.articles:
            continue

        # Source section header
        lines.append(f"{'=' * 50}")
        lines.append(f"  {result.source.name}")
        lines.append(f"{'=' * 50}")
        lines.append("")

        for article in result.articles:
            lines.append(f"  • {article.title}")
            if article.description:
                # Indent the description for visual hierarchy
                for desc_line in article.description.split("\n"):
                    lines.append(f"    {desc_line}")
            lines.append(f"    → {article.link}")
            lines.append("")

        lines.append("")

    # Footer
    lines.append("—")
    lines.append("Sent automatically by your News Digest bot.")
    lines.append("Manage your sources by re-running: ./start.sh")

    return "\n".join(lines)


def build_html(results: list[SourceResult]) -> str:
    """
    Build the HTML version of the multi-source digest email.

    Each source gets its own styled section with a colored header.
    Articles are displayed as cards with title, description, and link.
    """
    greeting = _time_greeting()
    date = _edition_date()
    greeting_html = _escape_html_text(greeting)
    date_html = _escape_html_text(date)

    # Build HTML blocks for each source
    source_blocks = []

    # Colors for source section headers (cycles if more than 4 sources)
    colors = ["#0066cc", "#d35400", "#27ae60", "#8e44ad"]

    for i, result in enumerate(results):
        color = colors[i % len(colors)]

        if result.error:
            source_name = _escape_html_text(result.source.name)
            error_html = _escape_html_text(result.error)
            source_blocks.append(f"""
    <div style="margin-bottom:24px;padding:12px 16px;background:#fff3cd;border-left:4px solid #ffc107;border-radius:4px;">
      <strong>⚠ {source_name}</strong> — {error_html}
    </div>""")
            continue

        if result.no_new_today:
            source_name = _escape_html_text(result.source.name)
            source_blocks.append(f"""
    <div style="margin-bottom:32px;">
      <div style="background:{color};color:white;padding:10px 16px;border-radius:6px 6px 0 0;">
        <h2 style="margin:0;font-size:16px;font-weight:bold;">{source_name}</h2>
      </div>
      <div style="border:1px solid #e0e0e0;border-top:none;border-radius:0 0 6px 6px;padding:24px 16px;text-align:center;">
        <p style="margin:0;color:#888;font-size:14px;font-style:italic;">No new articles published today.</p>
      </div>
    </div>""")
            continue

        if not result.articles:
            continue

        # Build article cards for this source
        article_cards = []
        for article in result.articles:
            title_html = _escape_html_text(article.title)
            desc_html = _escape_html_text(article.description).replace("\n", "<br>") if article.description else ""
            desc_block = f'<p style="margin:4px 0 8px 0;color:#555;font-size:14px;line-height:1.5;">{desc_html}</p>' if desc_html else ""
            link_href = _safe_href(article.link)
            if link_href:
                link_block = f'<a href="{link_href}" style="color:{color};font-size:13px;font-weight:bold;text-decoration:none;">Read full article →</a>'
            else:
                link_block = '<span style="color:#777;font-size:13px;">Link unavailable</span>'

            article_cards.append(f"""
      <div style="margin-bottom:16px;padding-bottom:16px;border-bottom:1px solid #f0f0f0;">
        <h3 style="margin:0 0 4px 0;font-size:15px;color:#1a1a2e;">{title_html}</h3>
        {desc_block}
        {link_block}
      </div>""")

        source_name = _escape_html_text(result.source.name)
        source_blocks.append(f"""
    <div style="margin-bottom:32px;">
      <div style="background:{color};color:white;padding:10px 16px;border-radius:6px 6px 0 0;">
        <h2 style="margin:0;font-size:16px;font-weight:bold;">{source_name}</h2>
      </div>
      <div style="border:1px solid #e0e0e0;border-top:none;border-radius:0 0 6px 6px;padding:16px;">
        {"".join(article_cards)}
      </div>
    </div>""")

    html_body = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width:680px; margin:0 auto; padding:20px; color:#222; background:#fafafa;">

  <div style="background:white;border-radius:8px;padding:24px;box-shadow:0 1px 3px rgba(0,0,0,0.1);">

    <p style="font-size:16px;margin-top:0;">{greeting_html},</p>
    <p style="font-size:16px;">Your news digest for <strong>{date_html}</strong>:</p>

    <hr style="border:none;border-top:2px solid #eee;margin:20px 0;">

{"".join(source_blocks)}

    <hr style="border:none;border-top:1px solid #eee;margin:20px 0;">
    <p style="font-size:11px;color:#999;text-align:center;">
      Sent automatically by your News Digest bot.<br>
      Manage your sources by re-running: <code>./start.sh</code>
    </p>

  </div>

</body>
</html>"""

    return html_body


def send_email(results: list[SourceResult]) -> None:
    """
    Format and send the multi-source digest email via Gmail SMTP.

    1. Creates a multipart email container
    2. Builds both plain-text and HTML bodies
    3. Opens a TLS connection to Gmail
    4. Authenticates and sends
    """
    # Build the email
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Your News Digest — {_edition_date()}"
    msg["From"] = SMTP_EMAIL
    msg["To"] = RECIPIENT_EMAIL

    plain = build_plain_text(results)
    html = build_html(results)

    # Plain text first, HTML second (email clients prefer the last part)
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html, "html"))

    # Send via Gmail SMTP with TLS
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_APP_PASSWORD)
        server.sendmail(SMTP_EMAIL, RECIPIENT_EMAIL, msg.as_string())

    print(f"  ✔ Email sent to {RECIPIENT_EMAIL}")
