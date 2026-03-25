#!/bin/bash
# setup.sh — Install dependencies and configure scheduling on macOS.
#
# Usage:
#   chmod +x setup.sh
#   ./setup.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLIST_NAME="com.acm.technews.email"
PLIST_SRC="$SCRIPT_DIR/$PLIST_NAME.plist"
PLIST_DEST="$HOME/Library/LaunchAgents/$PLIST_NAME.plist"

echo "=== ACM TechNews Email Automation Setup ==="
echo ""

# 1. Create virtual environment if needed
if [ ! -d "$SCRIPT_DIR/venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv "$SCRIPT_DIR/venv"
fi

echo "Installing dependencies..."
"$SCRIPT_DIR/venv/bin/pip" install -q -r "$SCRIPT_DIR/requirements.txt"

# 2. Check for .env file
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    echo ""
    echo "ERROR: No .env file found!"
    echo "Copy .env.example to .env and fill in your Gmail credentials:"
    echo "  cp .env.example .env"
    echo "  nano .env"
    exit 1
fi

# 3. Generate the launchd plist with the correct paths
PYTHON_PATH="$SCRIPT_DIR/venv/bin/python3"

cat > "$PLIST_SRC" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$PLIST_NAME</string>

    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON_PATH</string>
        <string>$SCRIPT_DIR/main.py</string>
    </array>

    <key>WorkingDirectory</key>
    <string>$SCRIPT_DIR</string>

    <!-- Run at 8:00 AM on Mon, Wed, Fri (ACM TechNews publish days) -->
    <key>StartCalendarInterval</key>
    <array>
        <dict>
            <key>Weekday</key>
            <integer>1</integer>
            <key>Hour</key>
            <integer>8</integer>
            <key>Minute</key>
            <integer>0</integer>
        </dict>
        <dict>
            <key>Weekday</key>
            <integer>3</integer>
            <key>Hour</key>
            <integer>8</integer>
            <key>Minute</key>
            <integer>0</integer>
        </dict>
        <dict>
            <key>Weekday</key>
            <integer>5</integer>
            <key>Hour</key>
            <integer>8</integer>
            <key>Minute</key>
            <integer>0</integer>
        </dict>
    </array>

    <key>StandardOutPath</key>
    <string>$SCRIPT_DIR/logs/stdout.log</string>

    <key>StandardErrorPath</key>
    <string>$SCRIPT_DIR/logs/stderr.log</string>
</dict>
</plist>
EOF

# 4. Create logs directory
mkdir -p "$SCRIPT_DIR/logs"

# 5. Install the launch agent
echo ""
echo "Installing launchd agent..."
cp "$PLIST_SRC" "$PLIST_DEST"
launchctl unload "$PLIST_DEST" 2>/dev/null || true
launchctl load "$PLIST_DEST"

echo ""
echo "=== Setup complete! ==="
echo ""
echo "Schedule: Mon, Wed, Fri at 8:00 AM (when ACM TechNews publishes)"
echo "The script skips sending if the same edition was already emailed."
echo ""
echo "Useful commands:"
echo "  Test now:          cd $SCRIPT_DIR && venv/bin/python3 main.py --dry-run"
echo "  Force send:        cd $SCRIPT_DIR && venv/bin/python3 main.py --force"
echo "  View logs:         cat $SCRIPT_DIR/logs/stdout.log"
echo "  Uninstall:         launchctl unload $PLIST_DEST && rm $PLIST_DEST"
