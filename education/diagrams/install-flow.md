# Install Flow Diagram

## macOS / Linux

```
User's terminal
  │
  ├─ curl -fsSL .../install.sh | bash
  │     │
  │     ├─ main() wrapper         ← curl|bash safety
  │     ├─ Download news-digest.zip (HTTPS)
  │     ├─ Download SHA256SUMS.txt (HTTPS)
  │     ├─ Verify checksum        ← shasum / sha256sum / openssl fallback
  │     │     └─ MISMATCH? → abort immediately
  │     ├─ Extract to ~/news-digest
  │     ├─ Run start.sh
  │     │     ├─ Detect OS (macOS vs Linux)
  │     │     ├─ Check/install Python 3
  │     │     ├─ Create venv
  │     │     ├─ pip install requirements.txt
  │     │     └─ Launch setup_wizard.py
  │     │           ├─ Step 1: Select news sources
  │     │           ├─ Step 2: Enter Gmail address
  │     │           ├─ Step 3: Enter App Password
  │     │           ├─ Step 4: Set schedule (optional)
  │     │           │     └─ scheduler.install_schedule()
  │     │           ├─ Write .env + chmod 600
  │     │           └─ Step 5: Send test email (optional)
  │     └─ Symlink news-digest → /usr/local/bin or ~/.local/bin
  │
  └─ Done! User types: news-digest
```

## Windows

```
User's PowerShell
  │
  ├─ irm .../install.ps1 | iex
  │     │
  │     ├─ Download news-digest.zip (Invoke-WebRequest)
  │     ├─ Download SHA256SUMS.txt
  │     ├─ Verify checksum (Get-FileHash -Algorithm SHA256)
  │     │     └─ MISMATCH? → abort immediately
  │     ├─ Extract to ~/news-digest (Expand-Archive)
  │     ├─ Check/install Python 3
  │     ├─ Create venv (python -m venv venv)
  │     ├─ pip install requirements.txt
  │     ├─ Launch setup_wizard.py
  │     │     └─ (same 5 steps as above)
  │     └─ Install-CommandWrapper
  │           ├─ Create news-digest.cmd in AppData\Local\NewsDigest\bin
  │           └─ Add to user PATH
  │
  └─ Done! User types: news-digest
```

## Trust Chain

Each step may only proceed if the previous step succeeded:

```
HTTPS download → Checksum match → Extract → Python found → Venv created → Wizard complete
```

A failure at any point aborts with a clear error message.
