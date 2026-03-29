# Scheduling Flow Diagram

## Installation

```
User chooses "Set delivery time" (wizard or CLI)
  │
  ├─ detect_os()
  │     ├─ "Darwin" → macOS
  │     ├─ "Linux"  → Linux
  │     ├─ "Windows"→ Windows
  │     └─ other    → "Unsupported OS"
  │
  ├─ macOS path:
  │     ├─ Build plist XML
  │     │     ├─ Label: com.newsdigest.daily
  │     │     ├─ ProgramArguments: [venv/bin/python3, main.py]
  │     │     ├─ WorkingDirectory: project root
  │     │     ├─ StartCalendarInterval: {Hour: H, Minute: M}
  │     │     └─ Log paths: logs/stdout.log, logs/stderr.log
  │     ├─ launchctl unload (if existing)
  │     ├─ Write plist to ~/Library/LaunchAgents/
  │     └─ launchctl load
  │
  ├─ Linux path:
  │     ├─ Build cron line: "M H * * * cd /path && python3 main.py >> log 2>> err # tag"
  │     ├─ Read current crontab
  │     ├─ Remove any existing newsdigest lines (by tag)
  │     ├─ Append new line
  │     └─ Write back via crontab -
  │
  └─ Windows path:
        ├─ schtasks /Delete (if existing, ignore errors)
        └─ schtasks /Create /TN "com.newsdigest.daily" /SC DAILY /ST HH:MM /F
```

## Daily Execution

```
OS scheduler fires at HH:MM
  │
  ├─ Invokes: /path/to/venv/python3 /path/to/main.py
  │     └─ (same runtime flow as manual run)
  │
  ├─ stdout → logs/stdout.log
  └─ stderr → logs/stderr.log
```

## Uninstallation

```
User chooses "Turn off schedule" (CLI option 7)
  │
  ├─ macOS: launchctl unload + delete plist file
  ├─ Linux: Read crontab, filter out tagged lines, write back
  └─ Windows: schtasks /Delete /TN "com.newsdigest.daily" /F
```

## Key Insight

The schedule is just the OS calling `main.py` — the same file you'd run
manually.  All the logic (fetch, filter, dedup, send) lives in main.py,
not in the scheduler.
