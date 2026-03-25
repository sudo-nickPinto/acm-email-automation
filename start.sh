#!/bin/bash
# =============================================================================
# start.sh — Bootstrap Script for News Digest (v3)
# =============================================================================
# This is the ONLY file your friend needs to run.
# It checks for Python, helps install it if missing, then sets everything up.
#
# Supports: macOS, Linux, and Windows (Git Bash / WSL)
#
# Usage:
#   chmod +x start.sh
#   ./start.sh
# =============================================================================

set -e

# ---------------------------------------------------------------------------
# Colors and formatting (makes the terminal output readable)
# ---------------------------------------------------------------------------
BOLD='\033[1m'
DIM='\033[2m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
banner() {
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}  $1${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

info() {
    echo -e "  ${BLUE}ℹ${NC}  $1"
}

success() {
    echo -e "  ${GREEN}✔${NC}  $1"
}

warn() {
    echo -e "  ${YELLOW}⚠${NC}  $1"
}

fail() {
    echo -e "  ${RED}✘${NC}  $1"
}

step() {
    echo ""
    echo -e "  ${BOLD}${CYAN}Step $1:${NC} ${BOLD}$2${NC}"
    echo -e "  ${DIM}─────────────────────────────────────────────${NC}"
}

prompt_continue() {
    echo ""
    echo -ne "  ${BOLD}Press Enter to continue (or Ctrl+C to quit)...${NC}"
    read -r
    echo ""
}

prompt_yes_no() {
    local prompt_msg="$1"
    local answer
    while true; do
        echo -ne "  ${BOLD}${prompt_msg} [y/n]:${NC} "
        read -r answer
        case "$answer" in
            [Yy]|[Yy][Ee][Ss]) return 0 ;;
            [Nn]|[Nn][Oo]) return 1 ;;
            *) echo -e "  ${DIM}Please type y or n.${NC}" ;;
        esac
    done
}

# ---------------------------------------------------------------------------
# Minimum Python version we require
# ---------------------------------------------------------------------------
REQUIRED_MAJOR=3
REQUIRED_MINOR=10

# ---------------------------------------------------------------------------
# Detect the current OS
# ---------------------------------------------------------------------------
detect_os() {
    case "$(uname -s)" in
        Darwin*) echo "macos" ;;
        Linux*)  echo "linux" ;;
        MINGW*|MSYS*|CYGWIN*) echo "windows" ;;
        *)       echo "unknown" ;;
    esac
}

OS="$(detect_os)"

# ---------------------------------------------------------------------------
# Check if a python3 command exists and meets the version requirement
# ---------------------------------------------------------------------------
check_python() {
    local python_cmd="$1"

    # Does the command exist at all?
    if ! command -v "$python_cmd" &>/dev/null; then
        return 1
    fi

    # Get the version string (e.g., "Python 3.12.1")
    local version_output
    version_output="$("$python_cmd" --version 2>&1)"

    # Extract major and minor version numbers
    local major minor
    major="$(echo "$version_output" | sed -n 's/Python \([0-9]*\)\.\([0-9]*\).*/\1/p')"
    minor="$(echo "$version_output" | sed -n 's/Python \([0-9]*\)\.\([0-9]*\).*/\2/p')"

    # Validate we got numbers
    if [[ -z "$major" || -z "$minor" ]]; then
        return 1
    fi

    # Check version meets minimum
    if (( major > REQUIRED_MAJOR )) || (( major == REQUIRED_MAJOR && minor >= REQUIRED_MINOR )); then
        return 0
    fi

    return 1
}

# Try common python command names and return the first one that works
find_python() {
    for cmd in python3 python python3.13 python3.12 python3.11 python3.10; do
        if check_python "$cmd"; then
            echo "$cmd"
            return 0
        fi
    done
    return 1
}

# ---------------------------------------------------------------------------
# Welcome screen
# ---------------------------------------------------------------------------
clear
banner "Welcome to News Digest Setup"

echo -e "  This tool sends you a daily email digest of news articles"
echo -e "  from newspapers and sources you choose."
echo ""
echo -e "  ${DIM}This setup wizard will:${NC}"
echo -e "  ${DIM}  1. Make sure Python is installed on your computer${NC}"
echo -e "  ${DIM}  2. Install the required packages${NC}"
echo -e "  ${DIM}  3. Walk you through configuration${NC}"
echo -e "  ${DIM}  4. Optionally set up automatic daily delivery${NC}"
echo ""
echo -e "  ${DIM}Estimated time: 5–10 minutes${NC}"

prompt_continue

# ---------------------------------------------------------------------------
# Step 1: Check for Python
# ---------------------------------------------------------------------------
step "1" "Checking for Python ${REQUIRED_MAJOR}.${REQUIRED_MINOR}+"

PYTHON_CMD=""

if PYTHON_CMD="$(find_python)"; then
    PYTHON_VERSION="$("$PYTHON_CMD" --version 2>&1)"
    success "Found ${PYTHON_VERSION} (${PYTHON_CMD})"
    echo ""
else
    # -----------------------------------------------------------------------
    # Python not found — guide the user through installing it
    # -----------------------------------------------------------------------
    warn "Python ${REQUIRED_MAJOR}.${REQUIRED_MINOR}+ is not installed on your computer."
    echo ""
    echo -e "  ${BOLD}What is Python?${NC}"
    echo -e "  Python is a programming language that this tool is written in."
    echo -e "  You need it installed for the tool to work, but you don't need"
    echo -e "  to know how to code — this script handles everything."
    echo ""

    if [[ "$OS" == "macos" ]]; then
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # macOS installation flow
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        echo -e "  ${BOLD}How to install Python on macOS:${NC}"
        echo ""
        echo -e "  There are two options. Pick whichever is easier for you:"
        echo ""
        echo -e "  ${CYAN}Option A — Download from python.org (recommended for beginners)${NC}"
        echo -e "  ${DIM}────────────────────────────────────────────────────────────────${NC}"
        echo -e "    1. Open this URL in your browser:"
        echo ""
        echo -e "       ${BOLD}https://www.python.org/downloads/${NC}"
        echo ""
        echo -e "    2. Click the big yellow \"Download Python 3.x.x\" button"
        echo -e "    3. Open the downloaded .pkg file"
        echo -e "    4. Follow the installer (click Continue/Agree/Install)"
        echo -e "    5. When it finishes, come back here and press Enter"
        echo ""
        echo -e "  ${CYAN}Option B — Install via Homebrew (if you already have Homebrew)${NC}"
        echo -e "  ${DIM}────────────────────────────────────────────────────────────────${NC}"

        if command -v brew &>/dev/null; then
            echo -e "    ${GREEN}Homebrew is already installed on your system.${NC}"
            echo ""
            if prompt_yes_no "Install Python via Homebrew now?"; then
                echo ""
                info "Installing Python via Homebrew..."
                info "This may take a few minutes. Sit tight."
                echo ""
                brew install python@3
                echo ""

                # Re-check after install
                if PYTHON_CMD="$(find_python)"; then
                    PYTHON_VERSION="$("$PYTHON_CMD" --version 2>&1)"
                    success "Python installed successfully: ${PYTHON_VERSION}"
                else
                    fail "Something went wrong. Python was not found after install."
                    echo ""
                    info "Try Option A instead: download from https://www.python.org/downloads/"
                    info "Then re-run this script: ./start.sh"
                    exit 1
                fi
            else
                echo ""
                info "No problem. Use Option A above to install Python manually."
                echo ""
                echo -ne "  ${BOLD}After installing Python, press Enter to continue...${NC}"
                read -r
                echo ""

                # Re-check
                if PYTHON_CMD="$(find_python)"; then
                    PYTHON_VERSION="$("$PYTHON_CMD" --version 2>&1)"
                    success "Found ${PYTHON_VERSION}"
                else
                    fail "Python still not found."
                    echo ""
                    info "If you just installed it, try closing and reopening your terminal,"
                    info "then run this script again: ./start.sh"
                    exit 1
                fi
            fi
        else
            echo -e "    Homebrew is not installed on your system."
            echo -e "    If you want to use Homebrew, install it first by running:"
            echo ""
            echo -e "      ${DIM}/bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"${NC}"
            echo ""
            echo -e "    Then run: ${DIM}brew install python@3${NC}"
            echo ""
            echo -e "  ${BOLD}For most people, Option A (python.org download) is easiest.${NC}"
            echo ""
            echo -ne "  ${BOLD}After installing Python, press Enter to continue...${NC}"
            read -r
            echo ""

            # Re-check
            if PYTHON_CMD="$(find_python)"; then
                PYTHON_VERSION="$("$PYTHON_CMD" --version 2>&1)"
                success "Found ${PYTHON_VERSION}"
            else
                fail "Python still not found."
                echo ""
                info "If you just installed Python, you may need to:"
                info "  1. Close this terminal window completely"
                info "  2. Open a new terminal"
                info "  3. Navigate back here: cd $(pwd)"
                info "  4. Run again: ./start.sh"
                echo ""
                info "This is needed because your terminal doesn't know about"
                info "newly installed programs until it's restarted."
                exit 1
            fi
        fi

    elif [[ "$OS" == "linux" ]]; then
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Linux installation flow
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        echo -e "  ${BOLD}How to install Python on Linux:${NC}"
        echo ""
        echo -e "  Run one of these commands depending on your system:"
        echo ""
        echo -e "  ${DIM}Ubuntu/Debian:${NC}  sudo apt update && sudo apt install python3 python3-venv"
        echo -e "  ${DIM}Fedora:${NC}         sudo dnf install python3"
        echo -e "  ${DIM}Arch:${NC}           sudo pacman -S python"
        echo ""

        if prompt_yes_no "Would you like this script to try installing it for you?"; then
            echo ""
            if command -v apt &>/dev/null; then
                info "Detected apt (Debian/Ubuntu). Installing..."
                sudo apt update && sudo apt install -y python3 python3-venv python3-pip
            elif command -v dnf &>/dev/null; then
                info "Detected dnf (Fedora). Installing..."
                sudo dnf install -y python3
            elif command -v pacman &>/dev/null; then
                info "Detected pacman (Arch). Installing..."
                sudo pacman -S --noconfirm python
            else
                fail "Could not detect your package manager."
                info "Please install Python 3.10+ manually, then re-run ./start.sh"
                exit 1
            fi

            echo ""
            if PYTHON_CMD="$(find_python)"; then
                PYTHON_VERSION="$("$PYTHON_CMD" --version 2>&1)"
                success "Python installed successfully: ${PYTHON_VERSION}"
            else
                fail "Installation may have failed. Please install Python manually."
                exit 1
            fi
        else
            echo ""
            echo -ne "  ${BOLD}After installing Python, press Enter to continue...${NC}"
            read -r
            echo ""

            if PYTHON_CMD="$(find_python)"; then
                PYTHON_VERSION="$("$PYTHON_CMD" --version 2>&1)"
                success "Found ${PYTHON_VERSION}"
            else
                fail "Python still not found. Please install it and re-run ./start.sh"
                exit 1
            fi
        fi

    elif [[ "$OS" == "windows" ]]; then
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Windows (Git Bash / MSYS2 / WSL) installation flow
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        echo -e "  ${BOLD}How to install Python on Windows:${NC}"
        echo ""
        echo -e "  ${CYAN}Option A — Download from python.org (recommended)${NC}"
        echo -e "  ${DIM}────────────────────────────────────────────────────${NC}"
        echo -e "    1. Open this URL in your browser:"
        echo ""
        echo -e "       ${BOLD}https://www.python.org/downloads/${NC}"
        echo ""
        echo -e "    2. Click the big yellow \"Download Python 3.x.x\" button"
        echo -e "    3. Run the downloaded .exe file"
        echo -e "    4. ${RED}IMPORTANT:${NC} Check \"${BOLD}Add Python to PATH${NC}\" at the bottom!"
        echo -e "    5. Click \"Install Now\""
        echo -e "    6. When it finishes, ${BOLD}close and reopen${NC} your terminal"
        echo -e "    7. Come back to this directory and run: ${DIM}./start.sh${NC}"
        echo ""
        echo -e "  ${CYAN}Option B — Install via winget (if you have it)${NC}"
        echo -e "  ${DIM}────────────────────────────────────────────────────${NC}"
        echo -e "    Run: ${DIM}winget install Python.Python.3.12${NC}"
        echo -e "    Then close and reopen your terminal."
        echo ""
        echo -ne "  ${BOLD}After installing Python, press Enter to continue...${NC}"
        read -r
        echo ""

        if PYTHON_CMD="$(find_python)"; then
            PYTHON_VERSION="$("$PYTHON_CMD" --version 2>&1)"
            success "Found ${PYTHON_VERSION}"
        else
            fail "Python still not found."
            echo ""
            info "If you just installed Python, close this terminal completely"
            info "and open a new one, then run: ./start.sh"
            exit 1
        fi
    else
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Unknown OS
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        fail "Could not detect your operating system."
        echo ""
        info "Please install Python ${REQUIRED_MAJOR}.${REQUIRED_MINOR}+ from:"
        info "  https://www.python.org/downloads/"
        info "Then re-run: ./start.sh"
        exit 1
    fi
fi

# ---------------------------------------------------------------------------
# Step 2: Create virtual environment and install dependencies
# ---------------------------------------------------------------------------
step "2" "Setting up the project"

VENV_DIR="$SCRIPT_DIR/venv"

if [ ! -d "$VENV_DIR" ]; then
    info "Creating an isolated Python environment..."
    "$PYTHON_CMD" -m venv "$VENV_DIR"
    success "Environment created."
else
    success "Environment already exists."
fi

# Determine the correct venv binary path (Windows vs Unix)
if [[ "$OS" == "windows" ]]; then
    VENV_PIP="$VENV_DIR/Scripts/pip"
    VENV_PYTHON_BIN="$VENV_DIR/Scripts/python"
else
    VENV_PIP="$VENV_DIR/bin/pip"
    VENV_PYTHON_BIN="$VENV_DIR/bin/python3"
fi

info "Installing required packages (this takes a moment)..."
"$VENV_PIP" install -q --upgrade pip 2>/dev/null
"$VENV_PIP" install -q -r "$SCRIPT_DIR/requirements.txt"
success "All packages installed."

# ---------------------------------------------------------------------------
# Step 3: Create logs directory
# ---------------------------------------------------------------------------
mkdir -p "$SCRIPT_DIR/logs"

# ---------------------------------------------------------------------------
# Step 3: Launch the interactive setup wizard
# ---------------------------------------------------------------------------
# The wizard is a Python script that handles:
#   - Newspaper source selection
#   - Gmail credential setup
#   - Writing the .env file
#   - Sending a test email
# ---------------------------------------------------------------------------
"$VENV_PYTHON_BIN" "$SCRIPT_DIR/setup_wizard.py"
