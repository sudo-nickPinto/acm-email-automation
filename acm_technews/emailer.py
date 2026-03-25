# =============================================================================
# emailer.py — Email Formatter and Sender
# =============================================================================
#
# This module takes a list of Article objects (produced by scraper.py) and
# turns them into a nicely formatted email that gets delivered through Gmail's
# SMTP server.
#
# Why a separate emailer module?
# ------------------------------
# Same reason as the scraper: Single Responsibility.  If we ever want to
# switch from Gmail to SendGrid, Mailgun, or Amazon SES, only this file
# needs to change.  The scraper and main.py don't care how email gets sent.
#
# Email format:
# -------------
# We send a "multipart/alternative" email, which means we include BOTH a
# plain-text version and an HTML version of the same content.  The
# recipient's email client picks whichever it prefers (most will show HTML).
# Including both is considered best practice — it ensures the email is
# readable even in terminal-based email clients (mutt, alpine) or if images
# are blocked.
#
# SMTP crash course:
# ------------------
# SMTP is the protocol for sending email.  Here's the sequence:
#   1. Open a TCP connection to smtp.gmail.com on port 587
#   2. Upgrade to TLS encryption (STARTTLS)
#   3. Authenticate with username + app password
#   4. Send the email data (headers + body)
#   5. Close the connection
# Python's smtplib handles all of this — we just call the right methods.
#
# Dependencies:
#   smtplib, datetime, email.mime — all stdlib (no pip install needed)
#   config — our local configuration module
#   scraper — for the Article dataclass type hint
# =============================================================================

"""
Email sender module — formats and sends the ACM TechNews digest.
"""

# smtplib is Python's built-in SMTP (email sending) client.  It handles the
# low-level socket connection, TLS negotiation, and SMTP protocol commands.
import smtplib

# datetime lets us get the current date/time so we can generate a
# time-appropriate greeting ("Good morning" vs "Good evening") and format
# the edition date for the subject line and body.
from datetime import datetime

# MIMEMultipart creates an email container that can hold multiple versions
# of the same content (plain text + HTML).  MIMEText wraps a string as a
# MIME-encoded email body part.
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Import all our SMTP and recipient settings from the central config file.
# This is the only place in the emailer that touches configuration.
from acm_technews.config import RECIPIENT_EMAIL, SMTP_APP_PASSWORD, SMTP_EMAIL, SMTP_PORT, SMTP_SERVER

# We import the Article dataclass so we can use it as a type hint.
# This makes the function signatures self-documenting.
from acm_technews.scraper import Article


def _time_greeting() -> str:
    """
    Return a time-appropriate greeting based on the current hour.

    This small touch makes the email feel less robotic.
    Before noon → "Good morning", before 5 PM → "Good afternoon",
    after 5 PM → "Good evening".
    """
    # Get the current hour in 24-hour format (0–23)
    hour = datetime.now().hour

    # Choose a greeting based on time of day
    if hour < 12:
        return "Good morning"
    elif hour < 17:
        return "Good afternoon"
    else:
        return "Good evening"


def _edition_date() -> str:
    """
    Return today's date in a human-friendly format like "March 25, 2026".

    strftime format codes:
      %B = full month name, %d = day of month, %Y = 4-digit year
    """
    return datetime.now().strftime("%B %d, %Y")


def build_plain_text(articles: list[Article]) -> str:
    """
    Build the plain-text version of the email.

    This version is shown by email clients that don't render HTML (rare, but
    it happens) and is also used by the --dry-run flag in main.py to preview
    the email in the terminal without actually sending it.

    Structure:
      1. Greeting + date
      2. "Headlines at a Glance" — bullet list of all titles
      3. Detailed blurbs — each article with its summary and link
      4. Footer
    """
    # Get the dynamic greeting and today's formatted date
    greeting = _time_greeting()
    date = _edition_date()

    # Start building the email line by line — we'll join them at the end
    lines = [
        f"{greeting},",                          # e.g., "Good morning,"
        "",                                       # blank line for spacing
        f"The {date} edition of ACM TechNews:",   # edition header
        "",
        "=" * 50,                                 # visual separator
        "HEADLINES AT A GLANCE:",                  # section title
        "=" * 50,
        "",
    ]

    # Headlines block — just the titles in a bullet list for quick scanning
    for article in articles:
        lines.append(f"  • {article.title}")

    # Close out the headlines section
    lines.append("")
    lines.append("=" * 50)
    lines.append("")

    # Detailed blurbs — each article gets a title, underline, blurb, and link
    for article in articles:
        lines.append(article.title)
        # Underline the title with dashes (same length) for visual structure
        lines.append("-" * len(article.title))
        lines.append(article.blurb)
        lines.append("")
        # Indented link to the full article
        lines.append(f"  [ » Read full article: {article.link} ]")
        # Include the source attribution if we have one
        if article.source:
            lines.append(f"  {article.source}")
        lines.append("")
        lines.append("")  # double blank line between articles

    # Footer — identifies this as an automated message
    lines.append("—")
    lines.append("Sent automatically from your ACM TechNews digest bot.")

    # Join all lines with newlines and return the complete plain-text body
    return "\n".join(lines)


def build_html(articles: list[Article]) -> str:
    """
    Build the HTML version of the email.

    Most email clients will display this version.  Inline CSS is used
    everywhere because email clients strip <style> blocks and ignore
    external stylesheets — inline styles are the only reliable approach.

    The structure mirrors the plain-text version:
      1. Greeting + date
      2. Headlines (ordered list in a blue-accented box)
      3. Detailed article cards
      4. Footer
    """
    # Get the same greeting and date used in the plain-text version
    greeting = _time_greeting()
    date = _edition_date()

    # Build the <li> items for the headlines ordered list
    headlines_li = "\n".join(
        f'        <li style="margin-bottom:4px;">{a.title}</li>' for a in articles
    )

    # Build a detailed HTML block for each article
    article_blocks = []
    for a in articles:
        # Convert newlines in the blurb to <br> tags for HTML rendering
        blurb_html = a.blurb.replace("\n", "<br>")

        # Only include the source line if we have one
        source_html = f'<div style="color:#888;font-size:13px;margin-top:4px;">{a.source}</div>' if a.source else ""

        # Each article is a <div> block with the title, blurb, link, and source
        article_blocks.append(f"""
    <div style="margin-bottom:24px;">
      <h3 style="margin:0 0 6px 0;color:#1a1a2e;">{a.title}</h3>
      <p style="margin:0 0 8px 0;color:#333;line-height:1.5;">{blurb_html}</p>
      <a href="{a.link}" style="color:#0066cc;font-weight:bold;">» Read full article</a>
      {source_html}
    </div>""")

    # Assemble the full HTML document
    # We use inline styles on every element because email clients strip
    # <style> blocks and <link> stylesheets for security reasons.
    html_body = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: Georgia, 'Times New Roman', serif; max-width:680px; margin:0 auto; padding:20px; color:#222;">

  <p style="font-size:16px;">{greeting},</p>
  <p style="font-size:16px;">The <strong>{date}</strong> edition of <strong>ACM TechNews</strong>:</p>

  <div style="background:#f4f4f8; border-left:4px solid #0066cc; padding:16px 20px; margin:20px 0;">
    <h2 style="margin:0 0 12px 0; font-size:18px; color:#1a1a2e;">HEADLINES AT A GLANCE:</h2>
    <ol style="margin:0; padding-left:20px;">
{headlines_li}
    </ol>
  </div>

  <hr style="border:none;border-top:2px solid #ddd;margin:24px 0;">

{"".join(article_blocks)}

  <hr style="border:none;border-top:1px solid #eee;margin:24px 0;">
  <p style="font-size:12px;color:#999;">Sent automatically from your ACM TechNews digest bot.</p>

</body>
</html>"""

    return html_body


def send_email(articles: list[Article]) -> None:
    """
    Format and send the ACM TechNews digest email via Gmail SMTP.

    This is the top-level function that main.py calls.  It:
      1. Creates a multipart email container
      2. Builds both plain-text and HTML bodies
      3. Opens a TLS connection to Gmail
      4. Authenticates and sends the message
    """
    # Create a MIME "alternative" container — this tells the email client
    # that the plain-text and HTML parts are two representations of the
    # same content, and the client should pick the best one to display.
    msg = MIMEMultipart("alternative")

    # Set the standard email headers
    msg["Subject"] = "Tech News for the Day"
    msg["From"] = SMTP_EMAIL
    msg["To"] = RECIPIENT_EMAIL

    # Build both versions of the email body
    plain = build_plain_text(articles)
    html = build_html(articles)

    # Attach both versions to the message.  The order matters: email clients
    # prefer the last part, so HTML goes second to be displayed by default.
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html, "html"))

    # Open a connection to Gmail's SMTP server.  The `with` statement ensures
    # the connection is cleanly closed even if an error occurs mid-send.
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        # Upgrade the connection from plain text to TLS (encrypted).
        # Without this, our password would be sent in cleartext over the wire.
        server.starttls()

        # Authenticate with our Gmail address and the app-specific password
        server.login(SMTP_EMAIL, SMTP_APP_PASSWORD)

        # Send the email.  msg.as_string() serializes the entire MIME
        # message (headers + both body parts) into a single string.
        server.sendmail(SMTP_EMAIL, RECIPIENT_EMAIL, msg.as_string())

    # Confirm in the console that the email was sent successfully
    print(f"Email sent to {RECIPIENT_EMAIL}")
