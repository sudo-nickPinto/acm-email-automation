# Lesson 05 — Install Flow and Release Artifacts

## Overview

The install flow has two sides: the **build side** (the developer runs `build_release.py` to create distributable assets) and the **install side** (the user runs `install.sh` or `install.ps1` to download and set up the tool).

## Build side: build_release.py

`scripts/build_release.py` creates the `dist/` folder with everything needed for a GitHub Release.

### What it produces

```
dist/
  news-digest.zip     The distributable package
  SHA256SUMS.txt      Checksums for verification
  install.sh          Copy of the macOS/Linux installer
  install.ps1         Copy of the Windows installer
  SHARE_THIS.txt      Instructions for uploading to GitHub
```

### How it works, line by line

**Step 1 — Clean worktree check:**
```python
def ensure_clean_worktree() -> None:
    # Runs: git status --porcelain --untracked-files=no
    # If any output exists, the worktree has uncommitted changes
    # Refuses to build to prevent shipping debug code
    # Override with NEWSDIGEST_ALLOW_DIRTY=1 for local testing
```

**Why?** Building a release from a dirty worktree means the package could contain uncommitted debug prints, half-finished features, or removed files. The check prevents accidental dirty releases. The environment variable escape hatch exists for CI smoke tests.

**Step 2 — File discovery:**
```python
def tracked_files() -> list[Path]:
    # Runs: git ls-files -z
    # Returns every file git is tracking (null-byte separated for safety)
    # Adds MANDATORY_PACKAGE_FILES even if not tracked yet
    # Filters through should_package()
```

The `-z` flag uses null bytes instead of newlines as separators, which correctly handles filenames containing spaces or special characters.

**Step 3 — Package filtering:**
```python
EXCLUDED_PREFIXES = (".github/", "dist/", "education/", "scripts/", "tests/")
EXCLUDED_FILES = {".gitignore", "install.sh", "install.ps1"}
MANDATORY_PACKAGE_FILES = (Path("news-digest.ps1"), Path("requirements.lock"), Path("newsdigest/paths.py"))
```

**Why these exclusions?**
- `.github/` — CI config, not needed by end users
- `dist/` — would be recursive (packaging the package)
- `education/` — teaching material, not runtime code
- `scripts/` — developer tooling, not user-facing
- `tests/` — test suite, not needed by end users
- `install.sh`/`install.ps1` — copied separately to dist/, not inside the zip
- `.gitignore` — git metadata, irrelevant to installed copy

**Why mandatory files?** Some files (like `news-digest.ps1` and `paths.py`) might be on a feature branch that has not been merged yet. The mandatory list ensures they are always included if they exist on disk, regardless of git tracking status.

**Step 4 — Zip creation:**
```python
def build_zip(files: list[Path]) -> Path:
    # Creates dist/news-digest.zip
    # Every file goes under a news-digest/ prefix inside the zip
    # Uses ZIP_DEFLATED compression
```

The `ZIP_ROOT = Path("news-digest")` prefix means when the zip is extracted, all files land inside a `news-digest/` folder. This is a packaging convention — the installer expects this structure and validates it.

**Step 5 — Checksum generation:**
```python
def write_checksums(paths: list[Path]) -> None:
    # For each file in dist/ (zip + installers):
    #   Compute SHA-256 hash
    #   Write: "hash  filename" to SHA256SUMS.txt
```

The checksum file follows the standard `sha256sum` format (`hash  filename`), so it can be verified with `sha256sum -c SHA256SUMS.txt` on Linux or parsed by the installer scripts.

## Install side: install.sh (macOS/Linux)

### The main() wrapper

The entire script is wrapped in a `main()` function:

```bash
main() {
    # ... entire script ...
}
main "$@"
```

**Why?** When a user runs `curl ... | bash`, bash reads from the pipe line by line. If the script does `exec < /dev/tty` (to read user input from the real terminal), that steals stdin away from bash mid-read, breaking the rest of the script. Wrapping everything in `main()` forces bash to read the entire script into memory first, then execute it.

### Configuration (environment variable overrides)

```bash
RELEASE_BASE_URL="${NEWSDIGEST_RELEASE_BASE_URL:-https://github.com/.../releases/latest/download}"
PACKAGE_URL="${NEWSDIGEST_PACKAGE_URL:-$RELEASE_BASE_URL/news-digest.zip}"
INSTALL_DIR="${NEWSDIGEST_INSTALL_DIR:-$HOME/news-digest}"
SKIP_LAUNCH="${NEWSDIGEST_SKIP_LAUNCH:-0}"
```

The `${VAR:-default}` syntax means "use `$VAR` if set, otherwise use `default`". This allows CI to override the download URL (pointing to a local HTTP server) and the install directory (using a temp folder) without modifying the script.

### SHA-256 verification with fallbacks

```bash
sha256_file() {
    if command -v shasum &>/dev/null; then
        shasum -a 256 "$target" | awk '{print $1}'
    elif command -v sha256sum &>/dev/null; then
        sha256sum "$target" | awk '{print $1}'
    elif command -v openssl &>/dev/null; then
        openssl dgst -sha256 "$target" | awk '{print $NF}'
    fi
}
```

**Why three tools?** Different systems have different hashing utilities:
- macOS ships `shasum` but not `sha256sum`
- Linux distros typically ship `sha256sum`
- Some minimal systems only have `openssl`

The script tries each in order and uses the first one that exists.

### Extraction validation

After unzipping, the installer validates the package structure:

```bash
# Must be exactly one top-level directory
TOP_LEVEL_ENTRY_COUNT="$(find "$EXTRACT_DIR" -mindepth 1 -maxdepth 1 | wc -l)"
# That directory must be named "news-digest"
if [ "$(basename "$EXTRACTED_FOLDER")" != "news-digest" ]; then ...
# Required files must exist
for required_path in start.sh news-digest setup_wizard.py; do ...
```

### CLI command installation

The script creates a symlink so users can type `news-digest` from anywhere:

```bash
if [ -d "/usr/local/bin" ] && [ -w "/usr/local/bin" ]; then
    ln -sf "$INSTALL_DIR/news-digest" /usr/local/bin/news-digest
else
    mkdir -p "$HOME/.local/bin"
    ln -sf "$INSTALL_DIR/news-digest" "$HOME/.local/bin/news-digest"
fi
```

**Why two locations?** `/usr/local/bin/` is in every user's PATH on macOS but requires write permission. On Linux, the user might not have write access to `/usr/local/bin/`, so we fall back to `~/.local/bin/` (and warn if it is not in PATH).

## Install side: install.ps1 (Windows)

The Windows installer follows the same logical steps but uses PowerShell cmdlets:

| Step | bash (install.sh) | PowerShell (install.ps1) |
|------|-------------------|--------------------------|
| Download | `curl -fsSL -o file url` | `Invoke-WebRequest -Uri url -OutFile file` |
| Checksum | `shasum -a 256` | `Get-FileHash -Algorithm SHA256` |
| Extract | `unzip -q` | `Expand-Archive` |
| CLI wrapper | symlink to `/usr/local/bin` | `.cmd` file in `AppData/Local/NewsDigest/bin` |
| PATH update | User adds to `.bashrc` | `[Environment]::SetEnvironmentVariable("Path", ..., "User")` |

### The .cmd wrapper pattern

On Windows, you cannot "symlink to a .ps1 script" the way you symlink a bash script on Unix. Instead, the installer creates a tiny `.cmd` file that calls PowerShell:

```cmd
@echo off
"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File "C:\Users\you\news-digest\news-digest.ps1" %*
```

This `.cmd` file is placed in `AppData\Local\NewsDigest\bin\` and that directory is added to the user's PATH.
