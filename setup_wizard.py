# =============================================================================
# setup_wizard.py — Interactive Terminal Setup Wizard (v3)
# =============================================================================
#
# This is the guided setup experience that runs after start.sh installs Python
# and creates the virtual environment.  It walks the user through:
#
#   1. Choosing which newspaper sources they want
#   2. Setting up their Gmail credentials (with clear instructions)
#   3. Writing the .env file automatically
#   4. Sending a test email to verify everything works
#   5. Setting up automatic daily scheduling (optional)
#
# Design philosophy:
# ------------------
# - Every prompt explains what it's asking and why
# - No jargon — "App Password" is explained, not assumed
# - Mistakes are recoverable — they can re-run the wizard anytime
# - Colors and formatting make the terminal output scannable
#
# This file is called by start.sh after the venv is ready:
#   venv/bin/python3 setup_wizard.py
#
# Dependencies:
#   newsdigest.sources    — the source registry
#   newsdigest.scheduler  — daily schedule installer
#   (everything else is stdlib)
# =============================================================================

"""
Interactive terminal setup wizard for the News Digest tool.
"""

import os
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# If stdin is not a terminal (e.g., inherited from a curl|bash pipe),
# reopen it from /dev/tty so that input() reads from the real terminal.
# ---------------------------------------------------------------------------
if not sys.stdin.isatty():
    sys.stdin = open("/dev/tty", "r")

# We import sources directly — this module has no dependencies beyond stdlib
from newsdigest.sources import AVAILABLE_SOURCES, NewsSource
from newsdigest.scheduler import install_schedule, uninstall_schedule, is_schedule_installed, detect_os


# ---------------------------------------------------------------------------
# Terminal formatting helpers
# ---------------------------------------------------------------------------

BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
RED = "\033[0;31m"
CYAN = "\033[0;36m"
BLUE = "\033[0;34m"
NC = "\033[0m"  # No Color


def banner(text: str) -> None:
    """Print a prominent section banner."""
    print()
    print(f"{CYAN}{'━' * 59}{NC}")
    print(f"{BOLD}  {text}{NC}")
    print(f"{CYAN}{'━' * 59}{NC}")
    print()


def info(text: str) -> None:
    print(f"  {BLUE}ℹ{NC}  {text}")


def success(text: str) -> None:
    print(f"  {GREEN}✔{NC}  {text}")


def warn(text: str) -> None:
    print(f"  {YELLOW}⚠{NC}  {text}")


def fail(text: str) -> None:
    print(f"  {RED}✘{NC}  {text}")


def step(num: int, text: str) -> None:
    """Print a step header."""
    print()
    print(f"  {BOLD}{CYAN}Step {num}:{NC} {BOLD}{text}{NC}")
    print(f"  {DIM}{'─' * 45}{NC}")


# ---------------------------------------------------------------------------
# Path to the .env file (same directory as this script, i.e., project root)
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).parent
ENV_FILE = PROJECT_ROOT / ".env"


def _prompt_sources() -> list[NewsSource]:
    """
    Display the available newspaper sources and let the user pick.

    Shows a numbered list. User enters numbers separated by spaces
    (e.g., "1 3 4") to select sources.  At least one must be selected.

    Returns:
        List of selected NewsSource objects.
    """
    step(1, "Choose your news sources")
    print()
    print(f"  Which newspaper digests would you like to receive?")
    print()

    # Display the numbered list
    for i, source in enumerate(AVAILABLE_SOURCES, start=1):
        print(f"    {BOLD}[{i}]{NC} {source.name}")
        print(f"        {DIM}{source.description}{NC}")
        print()

    # Get user selection
    while True:
        print(f"  Enter the numbers of the sources you want, separated by spaces.")
        print(f"  {DIM}Example: 1 3 4  (or 'all' for everything){NC}")
        print()
        raw = input(f"  {BOLD}Your choices:{NC} ").strip()

        if not raw:
            warn("Please select at least one source.")
            print()
            continue

        # Handle 'all' shortcut
        if raw.lower() == "all":
            selected = list(AVAILABLE_SOURCES)
            break

        # Parse numbers
        try:
            nums = [int(x) for x in raw.split()]
        except ValueError:
            warn("Please enter numbers only (e.g., 1 3 4).")
            print()
            continue

        # Validate range
        invalid = [n for n in nums if n < 1 or n > len(AVAILABLE_SOURCES)]
        if invalid:
            warn(f"Invalid choice(s): {invalid}. Choose from 1–{len(AVAILABLE_SOURCES)}.")
            print()
            continue

        if not nums:
            warn("Please select at least one source.")
            print()
            continue

        # Deduplicate while preserving order
        seen = set()
        selected = []
        for n in nums:
            if n not in seen:
                seen.add(n)
                selected.append(AVAILABLE_SOURCES[n - 1])

        break

    # Confirm selection
    print()
    success("You selected:")
    for s in selected:
        print(f"       • {s.name}")

    return selected


def _prompt_email() -> str:
    """
    Ask the user for their Gmail address.

    Validates basic email format.  The user sends the digest TO themselves,
    so this is both the sender and the recipient.
    """
    step(2, "Email setup")
    print()
    print(f"  The digest will be sent FROM and TO your Gmail address.")
    print(f"  (You'll email yourself the news digest.)")
    print()

    email_regex = re.compile(r"^[a-zA-Z0-9._%+-]+@gmail\.com$")

    while True:
        email = input(f"  {BOLD}Your Gmail address:{NC} ").strip()

        if not email:
            warn("Email cannot be empty.")
            continue

        if not email_regex.match(email):
            warn("Please enter a valid Gmail address (must end with @gmail.com).")
            print(f"  {DIM}Example: yourname@gmail.com{NC}")
            continue

        return email


def _prompt_app_password() -> str:
    """
    Walk the user through getting a Gmail App Password, then collect it.

    This is the trickiest part of setup for non-technical users.
    We explain every step in plain language.
    """
    step(3, "Gmail App Password")
    print()
    print(f"  {BOLD}What is an App Password?{NC}")
    print(f"  Gmail won't let apps use your regular password for security.")
    print(f"  Instead, you create a special 16-character password just for")
    print(f"  this tool.  Your regular password stays safe.")
    print()
    print(f"  {BOLD}How to get one (takes about 2 minutes):{NC}")
    print()
    print(f"    1. Open this link in your browser:")
    print()
    print(f"       {BOLD}https://myaccount.google.com/apppasswords{NC}")
    print()
    print(f"    2. You may need to sign in to your Google account")
    print()
    print(f"    3. If you see a message about 2-Step Verification:")
    print(f"       {DIM}You need to enable it first. Go to:{NC}")
    print(f"       {DIM}https://myaccount.google.com/signinoptions/two-step-verification{NC}")
    print(f"       {DIM}Follow the steps, then come back to the App Passwords page.{NC}")
    print()
    print(f"    4. Under 'App name', type:  {BOLD}News Digest{NC}")
    print()
    print(f"    5. Click {BOLD}Create{NC}")
    print()
    print(f"    6. Google will show you a 16-character password like:")
    print(f"       {DIM}abcd efgh ijkl mnop{NC}")
    print()
    print(f"    7. Copy that password and paste it below")
    print(f"       {DIM}(spaces don't matter — we'll handle them){NC}")
    print()

    while True:
        password = input(f"  {BOLD}Your App Password:{NC} ").strip()

        # Remove spaces (Google shows it as "abcd efgh ijkl mnop")
        password = password.replace(" ", "")

        if not password:
            warn("App Password cannot be empty.")
            continue

        if len(password) != 16:
            warn(f"App Passwords are exactly 16 characters. You entered {len(password)}.")
            print(f"  {DIM}Make sure you copied the full password from Google.{NC}")
            continue

        if not password.isalpha():
            warn("App Passwords contain only letters (no numbers or symbols).")
            continue

        return password


def _write_env(
    email: str,
    app_password: str,
    sources: list[NewsSource],
    schedule_time: str = "",
) -> None:
    """
    Write the .env file with the user's configuration.

    Format:
        SMTP_EMAIL=user@gmail.com
        SMTP_APP_PASSWORD=abcdefghijklmnop
        RECIPIENT_EMAIL=user@gmail.com
        SELECTED_SOURCES=acm_technews,bbc_tech
        SCHEDULE_TIME=08:00  (or empty if no schedule)
    """
    source_keys = ",".join(s.key for s in sources)

    env_content = f"""# News Digest Configuration
# Generated by setup wizard — re-run ./start.sh to change
SMTP_EMAIL={email}
SMTP_APP_PASSWORD={app_password}
RECIPIENT_EMAIL={email}
SELECTED_SOURCES={source_keys}
SCHEDULE_TIME={schedule_time}
"""

    ENV_FILE.write_text(env_content)
    success(f"Configuration saved to .env")


def _prompt_schedule() -> str:
    """
    Ask the user if they want automatic daily delivery.

    Returns:
        Time string like "08:00" if they want scheduling,
        or empty string "" if they decline.
    """
    step(4, "Automatic daily delivery")
    print()
    print(f"  Would you like to receive your digest {BOLD}automatically{NC}")
    print(f"  every day without having to run a command?")
    print()

    current_os = detect_os()
    if current_os == "macos":
        mechanism = "macOS LaunchAgent"
    elif current_os == "linux":
        mechanism = "cron job"
    elif current_os == "windows":
        mechanism = "Windows Task Scheduler"
    else:
        print(f"  {DIM}Automatic scheduling is not supported on your OS.{NC}")
        print(f"  {DIM}You can run the digest manually with: venv/bin/python3 main.py{NC}")
        return ""

    print(f"  {DIM}This will set up a {mechanism} on your computer.{NC}")
    print(f"  {DIM}Your computer needs to be on at the scheduled time.{NC}")
    print()

    while True:
        answer = input(f"  {BOLD}Enable daily delivery? [y/n]:{NC} ").strip().lower()
        if answer in ("n", "no"):
            print()
            info("No problem! You can always send manually with:")
            print(f"    {DIM}venv/bin/python3 main.py{NC}")
            return ""
        elif answer in ("y", "yes"):
            break
        else:
            print(f"  {DIM}Please type y or n.{NC}")

    # Ask what time
    print()
    print(f"  What time would you like your digest delivered?")
    print(f"  {DIM}Use 24-hour format (e.g., 08:00 for 8 AM, 18:30 for 6:30 PM){NC}")
    print()

    while True:
        time_input = input(f"  {BOLD}Delivery time [default: 08:00]:{NC} ").strip()

        if not time_input:
            time_input = "08:00"

        # Validate format
        import re as _re
        match = _re.match(r"^(\d{1,2}):(\d{2})$", time_input)
        if not match:
            warn("Please use HH:MM format (e.g., 08:00, 14:30).")
            continue

        hour = int(match.group(1))
        minute = int(match.group(2))

        if hour < 0 or hour > 23:
            warn("Hour must be between 0 and 23.")
            continue
        if minute < 0 or minute > 59:
            warn("Minute must be between 0 and 59.")
            continue

        # Install the schedule
        print()
        try:
            message = install_schedule(hour, minute)
            success(message)
        except (RuntimeError, ValueError) as e:
            fail(str(e))
            info("You can still run the digest manually.")
            return ""

        return f"{hour:02d}:{minute:02d}"


def _offer_test(email: str) -> None:
    """
    Offer to send a test email so the user can verify setup works.
    """
    step(5, "Test your setup")
    print()
    print(f"  Want to send a test email to {BOLD}{email}{NC} right now?")
    print(f"  {DIM}This will fetch real articles and send a digest.{NC}")
    print()

    while True:
        answer = input(f"  {BOLD}Send test email? [y/n]:{NC} ").strip().lower()
        if answer in ("y", "yes"):
            print()
            info("Sending test email...")
            print()

            # We need to reload the config since we just wrote the .env file.
            # The cleanest way is to run main.py as a subprocess so it loads
            # the fresh .env file.
            import subprocess
            venv_python = PROJECT_ROOT / "venv" / "bin" / "python3"
            result = subprocess.run(
                [str(venv_python), str(PROJECT_ROOT / "main.py")],
                cwd=str(PROJECT_ROOT),
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                print(result.stdout)
                success("Test email sent! Check your inbox.")
            else:
                print(result.stdout)
                if result.stderr:
                    print(result.stderr)
                fail("Something went wrong. See the error above.")
                print()
                info("Common fixes:")
                print(f"    • Make sure 2-Step Verification is enabled on your Google account")
                print(f"    • Regenerate the App Password and try again")
                print(f"    • Run {DIM}./start.sh{NC} to redo the setup")
            break

        elif answer in ("n", "no"):
            print()
            info("No problem! You can always test later with:")
            print(f"    {DIM}venv/bin/python3 main.py --dry-run{NC}  (preview only)")
            print(f"    {DIM}venv/bin/python3 main.py{NC}            (send for real)")
            break
        else:
            print(f"  {DIM}Please type y or n.{NC}")


def run_wizard() -> None:
    """
    Main wizard flow — called by start.sh after Python/venv is ready.
    """
    banner("News Digest — Setup Wizard")

    print(f"  This wizard will help you set up your personal news digest.")
    print(f"  You'll choose your newspapers, enter your Gmail, and you're done.")
    print()
    print(f"  {DIM}You can re-run this wizard anytime with: ./start.sh{NC}")
    print()

    # Check if .env already exists — offer to reconfigure
    if ENV_FILE.exists():
        warn("You already have a configuration file (.env).")
        print()
        while True:
            answer = input(f"  {BOLD}Do you want to reconfigure? [y/n]:{NC} ").strip().lower()
            if answer in ("y", "yes"):
                break
            elif answer in ("n", "no"):
                print()
                success("Keeping existing configuration. You're all set!")
                print()
                info("Commands:")
                print(f"    {DIM}venv/bin/python3 main.py --dry-run{NC}  — Preview digest")
                print(f"    {DIM}venv/bin/python3 main.py{NC}            — Send digest")
                print(f"    {DIM}./start.sh{NC}                          — Re-run setup")
                print()
                return
            else:
                print(f"  {DIM}Please type y or n.{NC}")

    # Step 1: Choose sources
    sources = _prompt_sources()

    # Step 2: Email
    email = _prompt_email()

    # Step 3: App Password
    app_password = _prompt_app_password()

    # Write the .env file (without schedule for now — test first)
    print()
    _write_env(email, app_password, sources)

    # Step 4: Schedule
    schedule_time = _prompt_schedule()

    # If they chose a schedule, update .env with the time
    if schedule_time:
        _write_env(email, app_password, sources, schedule_time)

    # Step 5: Offer test
    _offer_test(email)

    # Final success message
    banner("Setup Complete!")

    print(f"  {GREEN}Your news digest is ready to go.{NC}")
    print()
    print(f"  {BOLD}Quick reference:{NC}")
    print()
    if schedule_time:
        print(f"    {GREEN}Auto-delivery is ON — daily at {schedule_time}{NC}")
        print()
    print(f"    Send your digest now:")
    print(f"    {DIM}$ venv/bin/python3 main.py{NC}")
    print()
    print(f"    Preview without sending:")
    print(f"    {DIM}$ venv/bin/python3 main.py --dry-run{NC}")
    print()
    print(f"    Change your settings:")
    print(f"    {DIM}$ ./start.sh{NC}")
    print()


# ---------------------------------------------------------------------------
# Entry point — this file is run directly by start.sh
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try:
        run_wizard()
    except KeyboardInterrupt:
        print()
        print()
        info("Setup cancelled. Run ./start.sh to try again.")
        print()
        sys.exit(0)
