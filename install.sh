#!/bin/bash
# =============================================================================
# install.sh — One-Line Installer for News Digest (macOS / Linux)
# =============================================================================
#
# This script is designed to be piped from curl:
#   curl -fsSL https://raw.githubusercontent.com/sudo-nickPinto/acm-email-automation/public_attempt/install.sh | bash
#
# What it does:
#   1. Downloads the project as a zip from GitHub (no git required)
#   2. Extracts it to ~/news-digest
#   3. Launches the setup wizard (start.sh)
#
# No git, no GitHub account, no coding knowledge required.
# =============================================================================

set -e

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
REPO_URL="https://github.com/sudo-nickPinto/acm-email-automation/archive/refs/heads/public_attempt.zip"
INSTALL_DIR="$HOME/news-digest"
ZIP_FILE="/tmp/news-digest-download.zip"
EXTRACT_DIR="/tmp/news-digest-extract"

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

echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}  News Digest — Installer${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# ---------------------------------------------------------------------------
# Step 1: Check for curl (should be pre-installed on macOS and most Linux)
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
# Step 3: Download
# ---------------------------------------------------------------------------
echo -e "  ${CYAN}↓${NC}  Downloading News Digest..."

# Clean up any previous temp files
rm -f "$ZIP_FILE"
rm -rf "$EXTRACT_DIR"

curl -fsSL -o "$ZIP_FILE" "$REPO_URL"

if [ ! -f "$ZIP_FILE" ]; then
    echo -e "  ${RED}✘${NC}  Download failed. Check your internet connection."
    exit 1
fi

echo -e "  ${GREEN}✔${NC}  Downloaded."

# ---------------------------------------------------------------------------
# Step 4: Extract
# ---------------------------------------------------------------------------
echo -e "  ${CYAN}↓${NC}  Installing to ${BOLD}$INSTALL_DIR${NC}..."

mkdir -p "$EXTRACT_DIR"

# unzip is available on macOS by default, and most Linux distros
if command -v unzip &>/dev/null; then
    unzip -q "$ZIP_FILE" -d "$EXTRACT_DIR"
else
    # Fallback to Python's zipfile module (Python is usually available)
    python3 -c "
import zipfile, sys
with zipfile.ZipFile('$ZIP_FILE', 'r') as z:
    z.extractall('$EXTRACT_DIR')
" 2>/dev/null || {
        echo -e "  ${RED}✘${NC}  Cannot extract zip. Please install unzip:"
        echo -e "  ${DIM}Ubuntu/Debian: sudo apt install unzip${NC}"
        rm -f "$ZIP_FILE"
        exit 1
    }
fi

# GitHub zips extract into a folder named repo-branch, find it
EXTRACTED_FOLDER=$(find "$EXTRACT_DIR" -mindepth 1 -maxdepth 1 -type d | head -1)

if [ -z "$EXTRACTED_FOLDER" ]; then
    echo -e "  ${RED}✘${NC}  Extraction failed — no folder found."
    rm -f "$ZIP_FILE"
    rm -rf "$EXTRACT_DIR"
    exit 1
fi

# Move to the install location
mv "$EXTRACTED_FOLDER" "$INSTALL_DIR"

# Clean up temp files
rm -f "$ZIP_FILE"
rm -rf "$EXTRACT_DIR"

echo -e "  ${GREEN}✔${NC}  Installed to ${BOLD}$INSTALL_DIR${NC}"

# ---------------------------------------------------------------------------
# Step 5: Make scripts executable and launch setup
# ---------------------------------------------------------------------------
chmod +x "$INSTALL_DIR/start.sh"

echo ""
echo -e "  ${BOLD}Launching setup wizard...${NC}"
echo ""

cd "$INSTALL_DIR"
./start.sh < /dev/tty
