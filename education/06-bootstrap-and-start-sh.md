# Lesson 06 — Bootstrap and start.sh

## What start.sh does

`start.sh` is the bridge between the installer and the setup wizard. Its job is to ensure the Python environment is ready, then hand off to the Python wizard. It handles:

1. **stdin reconnection** for `curl | bash` invocations
2. **Python discovery** — finding Python 3.10+ on the system
3. **Python installation guidance** — OS-specific help if Python is missing
4. **Virtual environment creation** — `python3 -m venv venv`
5. **Dependency installation** — `pip install -r requirements.lock`
6. **Wizard launch** — `venv/bin/python3 setup_wizard.py`

## stdin reconnection

```bash
if [ ! -t 0 ]; then
    exec < /dev/tty
fi
```

**What this does:** When the user runs `curl ... | bash`, stdin is the pipe from curl, not the keyboard. The `[ ! -t 0 ]` test checks if file descriptor 0 (stdin) is a terminal. If it is not, `exec < /dev/tty` redirects stdin to the real terminal so that `read` prompts and Python's `input()` function work correctly.

**Why this matters:** Without this line, every `read` and `input()` call in the wizard would immediately get EOF (end of file) because the curl pipe is empty after the script finishes downloading. The user would see prompts flash by with no chance to type.

**Note:** This is different from the `main()` wrapper in `install.sh`. The wrapper solves "bash reads the script from stdin line by line." This `exec` solves "after bash finishes reading the script, stdin is still the pipe."

## Python discovery

```bash
REQUIRED_MAJOR=3
REQUIRED_MINOR=10

check_python() {
    local python_cmd="$1"
    if ! command -v "$python_cmd" &>/dev/null; then return 1; fi
    local version_output
    version_output="$("$python_cmd" --version 2>&1)"
    local major minor
    major="$(echo "$version_output" | sed -n 's/Python \([0-9]*\)\.\([0-9]*\).*/\1/p')"
    minor="$(echo "$version_output" | sed -n 's/Python \([0-9]*\)\.\([0-9]*\).*/\2/p')"
    if [[ -z "$major" || -z "$minor" ]]; then return 1; fi
    if (( major > REQUIRED_MAJOR )) || (( major == REQUIRED_MAJOR && minor >= REQUIRED_MINOR )); then
        return 0
    fi
    return 1
}

find_python() {
    for cmd in python3 python python3.13 python3.12 python3.11 python3.10; do
        if check_python "$cmd"; then echo "$cmd"; return 0; fi
    done
    return 1
}
```

**The strategy:** Try multiple command names in priority order. On macOS, the system python3 might be an old version, but `python3.12` (installed via Homebrew) would work. On Linux, `python3` is usually correct. The function tries each one and returns the first that meets the minimum version requirement.

**Why Python 3.10+?** The codebase uses `list[str]` and `str | None` type hint syntax introduced in Python 3.10. Older versions would crash with a `SyntaxError` on import, which would be confusing for non-technical users.

## OS-specific Python installation guidance

If `find_python` fails, `start.sh` detects the OS and prints tailored instructions:

- **macOS:** Suggests `brew install python3` (Homebrew) and provides a fallback to the python.org website
- **Linux:** Suggests `sudo apt install python3 python3-venv` (Debian/Ubuntu) or `sudo dnf install python3` (Fedora/RHEL)
- **Windows (Git Bash):** Suggests `winget install Python.Python.3.12` or downloading from python.org

The instructions are written for non-technical users — they explain what Python is ("a programming language this tool is written in"), emphasize the user does not need to know how to code, and include the exact commands to copy/paste.

## Virtual environment creation

```bash
"$PYTHON_CMD" -m venv venv
```

**What is a venv?** A virtual environment is a self-contained Python installation inside the `venv/` folder. It has its own `pip`, its own installed packages, and its own `python3` binary. This prevents conflicts with other Python projects on the same computer.

**Why does this matter?** If the user has another Python project that uses `requests` version 2.28, and we need version 2.31, a venv means both versions coexist without conflict. When the user uninstalls News Digest, they just delete the folder — no system-wide cleanup needed.

## Dependency installation

```bash
REQUIREMENTS_FILE="requirements.lock"
if [ ! -f "$REQUIREMENTS_FILE" ]; then
    REQUIREMENTS_FILE="requirements.txt"
fi

"$VENV_PIP" install --quiet -r "$REQUIREMENTS_FILE"
```

**Why `requirements.lock` first?** `requirements.lock` contains pinned versions (`requests==2.31.0`) for reproducible installs. `requirements.txt` uses ranges (`requests>=2.28`). The lock file is preferred because it guarantees the exact versions that were tested. Testing is done against the lock file in CI, so using it in production ensures consistency.

## Wizard launch

```bash
"$VENV_PYTHON" "$SCRIPT_DIR/setup_wizard.py"
```

At this point, Python is installed, the venv is ready, dependencies are installed, and we hand control to the Python wizard for interactive configuration.
