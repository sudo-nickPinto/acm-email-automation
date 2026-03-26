#!/bin/bash
# =============================================================================
# install.sh — One-Line Installer for News Digest (macOS / Linux)
# =============================================================================
#
# This script can be downloaded from a GitHub Release asset and run locally:
#   curl -fsSLO https://github.com/sudo-nickPinto/acm-email-automation/releases/latest/download/install.sh
#   bash install.sh
#
# Convenience-only shortcut:
#   curl -fsSL https://github.com/sudo-nickPinto/acm-email-automation/releases/latest/download/install.sh | bash
#
# What it does:
#   1. Downloads the packaged app zip from the latest GitHub Release
#   2. Verifies the download against SHA256SUMS.txt
#   3. Extracts it to ~/news-digest
#   4. Launches the setup wizard (start.sh)
#
# IMPORTANT: The entire script is wrapped in main() so that bash reads it
# fully into memory before executing. Without this, 'curl | bash' reads
# line-by-line from stdin, and 'exec < /dev/tty' would steal stdin away
# from bash mid-script, breaking everything.
# =============================================================================

main() {

set -euo pipefail

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
RELEASE_BASE_URL="${NEWSDIGEST_RELEASE_BASE_URL:-https://github.com/sudo-nickPinto/acm-email-automation/releases/latest/download}"
PACKAGE_URL="${NEWSDIGEST_PACKAGE_URL:-$RELEASE_BASE_URL/news-digest.zip}"
CHECKSUM_URL="${NEWSDIGEST_CHECKSUM_URL:-$RELEASE_BASE_URL/SHA256SUMS.txt}"
INSTALL_DIR="${NEWSDIGEST_INSTALL_DIR:-$HOME/news-digest}"
BIN_DIR="${NEWSDIGEST_BIN_DIR:-}"
SKIP_LAUNCH="${NEWSDIGEST_SKIP_LAUNCH:-0}"
TEMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/news-digest.XXXXXX")"
ZIP_FILE="$TEMP_ROOT/news-digest-download.zip"
CHECKSUM_FILE="$TEMP_ROOT/SHA256SUMS.txt"
EXTRACT_DIR="$TEMP_ROOT/extracted"

# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------
BOLD='\033[1m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
DIM='\033[2m'
NC='\033[0m'

download_file() {
    local url="$1"
    local dest="$2"
    curl -fsSL --retry 3 --retry-delay 1 -o "$dest" "$url"
}

sha256_file() {
    local target="$1"

    if command -v shasum &>/dev/null; then
        shasum -a 256 "$target" | awk '{print $1}'
        return 0
    fi

    if command -v sha256sum &>/dev/null; then
        sha256sum "$target" | awk '{print $1}'
        return 0
    fi

    if command -v openssl &>/dev/null; then
        openssl dgst -sha256 "$target" | awk '{print $NF}'
        return 0
    fi

    return 1
}

cleanup_temp() {
    rm -rf "$TEMP_ROOT"
}

trap cleanup_temp EXIT

echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}  News Digest — Installer${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# ---------------------------------------------------------------------------
# Step 1: Check for curl
# ---------------------------------------------------------------------------
if ! command -v curl &>/dev/null; then
    echo -e "  ${RED}✘${NC}  curl is not installed."
    echo -e "  ${DIM}Install it with your package manager and try again.${NC}"
    echo -e "  ${DIM}Ubuntu/Debian: sudo apt install curl${NC}"
    echo -e "  ${DIM}Fedora:        sudo dnf install curl${NC}"
    exit 1
fi

# ---------------------------------------------------------------------------
# Step 2: Check if already installed
# ---------------------------------------------------------------------------
if [ -d "$INSTALL_DIR" ]; then
    echo -e "  ${YELLOW}⚠${NC}  News Digest is already installed at ${BOLD}$INSTALL_DIR${NC}"
    echo ""
    echo -e "  To reconfigure, run:"
    echo -e "  ${DIM}cd $INSTALL_DIR && ./start.sh${NC}"
    echo ""
    echo -ne "  ${BOLD}Reinstall from scratch? [y/n]:${NC} "
    read -r answer < /dev/tty
    case "$answer" in
        [Yy]|[Yy][Ee][Ss])
            echo ""
            echo -e "  ${DIM}Removing old installation...${NC}"
            rm -rf "$INSTALL_DIR"
            ;;
        *)
            echo ""
            echo -e "  ${GREEN}✔${NC}  Keeping existing installation."
            echo -e "  ${DIM}Run: cd $INSTALL_DIR && ./start.sh${NC}"
            exit 0
            ;;
    esac
fi

# ---------------------------------------------------------------------------
# Step 3: Download + verify
# ---------------------------------------------------------------------------
echo -e "  ${CYAN}↓${NC}  Downloading News Digest..."

if ! download_file "$PACKAGE_URL" "$ZIP_FILE"; then
    echo -e "  ${RED}✘${NC}  Download failed."
    echo -e "  ${DIM}If you're the maintainer, upload dist/news-digest.zip to the latest GitHub Release.${NC}"
    exit 1
fi

if ! download_file "$CHECKSUM_URL" "$CHECKSUM_FILE"; then
    echo -e "  ${RED}✘${NC}  Could not download SHA256SUMS.txt."
    echo -e "  ${DIM}If you're the maintainer, upload dist/SHA256SUMS.txt to the latest GitHub Release.${NC}"
    cleanup_temp
    exit 1
fi

EXPECTED_HASH="$(awk '($2=="news-digest.zip" || $2=="*news-digest.zip") && $1 ~ /^[A-Fa-f0-9]{64}$/ {print tolower($1); exit}' "$CHECKSUM_FILE")"
if [ -z "$EXPECTED_HASH" ]; then
    echo -e "  ${RED}✘${NC}  SHA256SUMS.txt does not contain a valid checksum for news-digest.zip."
    cleanup_temp
    exit 1
fi

if ! ACTUAL_HASH="$(sha256_file "$ZIP_FILE")"; then
    echo -e "  ${RED}✘${NC}  No SHA-256 tool was found (need shasum, sha256sum, or openssl)."
    cleanup_temp
    exit 1
fi

if [ "$EXPECTED_HASH" != "$ACTUAL_HASH" ]; then
    echo -e "  ${RED}✘${NC}  Checksum verification failed."
    echo -e "  ${DIM}Expected: $EXPECTED_HASH${NC}"
    echo -e "  ${DIM}Actual:   $ACTUAL_HASH${NC}"
    cleanup_temp
    exit 1
fi

echo -e "  ${GREEN}✔${NC}  Downloaded and verified."

# ---------------------------------------------------------------------------
# Step 4: Extract
# ---------------------------------------------------------------------------
echo -e "  ${CYAN}↓${NC}  Installing to ${BOLD}$INSTALL_DIR${NC}..."

mkdir -p "$EXTRACT_DIR"

if command -v unzip &>/dev/null; then
    unzip -q "$ZIP_FILE" -d "$EXTRACT_DIR"
else
    python3 -c "
import zipfile
with zipfile.ZipFile('$ZIP_FILE', 'r') as z:
    z.extractall('$EXTRACT_DIR')
" 2>/dev/null || {
        echo -e "  ${RED}✘${NC}  Cannot extract zip. Please install unzip:"
        echo -e "  ${DIM}Ubuntu/Debian: sudo apt install unzip${NC}"
        cleanup_temp
        exit 1
    }
fi

TOP_LEVEL_ENTRY_COUNT="$(find "$EXTRACT_DIR" -mindepth 1 -maxdepth 1 | wc -l | tr -d ' ')"
TOP_LEVEL_DIR_COUNT="$(find "$EXTRACT_DIR" -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')"
EXTRACTED_FOLDER="$(find "$EXTRACT_DIR" -mindepth 1 -maxdepth 1 -type d | head -1)"

if [ "$TOP_LEVEL_ENTRY_COUNT" -ne 1 ] || [ "$TOP_LEVEL_DIR_COUNT" -ne 1 ]; then
    echo -e "  ${RED}✘${NC}  Extraction failed — expected a single top-level news-digest/ folder."
    cleanup_temp
    exit 1
fi

if [ "$(basename "$EXTRACTED_FOLDER")" != "news-digest" ]; then
    echo -e "  ${RED}✘${NC}  Extraction failed — package root must be news-digest/."
    cleanup_temp
    exit 1
fi

for required_path in start.sh news-digest setup_wizard.py; do
    if [ ! -e "$EXTRACTED_FOLDER/$required_path" ]; then
        echo -e "  ${RED}✘${NC}  Extraction failed — package is missing $required_path."
        cleanup_temp
        exit 1
    fi
done

mv "$EXTRACTED_FOLDER" "$INSTALL_DIR"

echo -e "  ${GREEN}✔${NC}  Installed to ${BOLD}$INSTALL_DIR${NC}"

# ---------------------------------------------------------------------------
# Step 5: Make scripts executable and install CLI command
# ---------------------------------------------------------------------------
chmod +x "$INSTALL_DIR/start.sh"
chmod +x "$INSTALL_DIR/news-digest"

if [ -n "$BIN_DIR" ]; then
    mkdir -p "$BIN_DIR"
    ln -sf "$INSTALL_DIR/news-digest" "$BIN_DIR/news-digest"
    echo -e "  ${GREEN}✔${NC}  Installed ${BOLD}news-digest${NC} command to $BIN_DIR"
elif [ -d "/usr/local/bin" ] && [ -w "/usr/local/bin" ]; then
    ln -sf "$INSTALL_DIR/news-digest" /usr/local/bin/news-digest
    echo -e "  ${GREEN}✔${NC}  Installed ${BOLD}news-digest${NC} command"
else
    mkdir -p "$HOME/.local/bin"
    ln -sf "$INSTALL_DIR/news-digest" "$HOME/.local/bin/news-digest"
    echo -e "  ${GREEN}✔${NC}  Installed ${BOLD}news-digest${NC} command to ~/.local/bin"
    case ":$PATH:" in
        *":$HOME/.local/bin:"*) ;;
        *)
            echo -e "  ${YELLOW}⚠${NC}  ~/.local/bin is not in your PATH."
            echo -e "  ${DIM}Add this line to your ~/.bashrc or ~/.zshrc:${NC}"
            echo -e "  ${DIM}  export PATH=\"\$HOME/.local/bin:\$PATH\"${NC}"
            ;;
    esac
fi

if [ "$SKIP_LAUNCH" = "1" ]; then
    echo ""
    echo -e "  ${DIM}Skipping setup wizard launch (NEWSDIGEST_SKIP_LAUNCH=1).${NC}"
    exit 0
fi

echo ""
echo -e "  ${BOLD}Launching setup wizard...${NC}"
echo ""

exec < /dev/tty

cd "$INSTALL_DIR"
exec bash ./start.sh

}

main "$@"
