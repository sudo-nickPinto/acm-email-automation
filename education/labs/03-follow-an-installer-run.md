# Lab 03: Follow an Installer Run

## Goal

Understand the secure install path — what happens from the moment a
friend pastes the install command until the setup wizard launches.

## Steps

### macOS/Linux Path

1. Open `install.sh`.  Note the `main() { ... } ; main` pattern.
   **Why?**  When piped via `curl | bash`, bash executes lines as they
   arrive.  Wrapping in a function ensures the entire script is loaded
   before execution starts.

2. Trace the download sequence:
   - `curl` downloads `news-digest.zip` and `SHA256SUMS.txt`
   - Both use HTTPS (TLS verification)

3. Find the checksum verification:
   ```bash
   EXPECTED=$(grep "news-digest.zip" "$SHA_FILE" | awk '{print $1}')
   ACTUAL=$(shasum -a 256 "$ZIP_FILE" | awk '{print $1}')
   ```
   Note the fallback chain: `shasum` → `sha256sum` → `openssl dgst`

4. Find where extraction happens.  Note it's **after** verification.

5. Find the symlink creation.  Note the fallback:
   `/usr/local/bin` (with sudo) → `~/.local/bin` (without sudo)

### Windows Path

6. Open `install.ps1`.  Trace the same sequence:
   - `Invoke-WebRequest` for downloads
   - `Get-FileHash -Algorithm SHA256` for checksum
   - `Expand-Archive` for extraction
   - `Install-CommandWrapper` for PATH setup

## Questions

1. What happens if the checksum doesn't match?
2. What happens if Python isn't installed?
3. Why are the installers separate from the zip (not inside it)?
4. What does `NEWSDIGEST_SKIP_LAUNCH=1` do and when is it used?
