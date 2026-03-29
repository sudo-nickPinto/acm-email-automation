# Lesson 13 — Scheduling and Automation

> **Goal:** Understand how `newsdigest/scheduler.py` installs daily
> automatic delivery on macOS, Linux, and Windows — and why each
> OS needs a completely different approach.

---

## 1  Purpose

The scheduler makes the digest **automatic**.  Instead of running
`main.py` every morning, the user sets a time once and the OS handles
the rest.

---

## 2  The Three Backends

| OS | Mechanism | Configuration |
|----|-----------|--------------|
| macOS | LaunchAgent (launchd) | XML plist file |
| Linux | cron (user-level) | crontab entry |
| Windows | Task Scheduler | schtasks.exe command |

All are **user-level** — no root/admin required.

---

## 3  OS Detection

```python
def detect_os() -> str:
    system = platform.system()
    if system == "Darwin":
        return "macos"
    elif system == "Linux":
        return "linux"
    elif system == "Windows":
        return "windows"
    return "unknown"
```

`platform.system()` returns the kernel name.  macOS reports "Darwin"
(its Unix kernel).

---

## 4  macOS — LaunchAgent

### 4.1  What is a LaunchAgent?

`launchd` is macOS's process manager (like systemd on Linux).  A
**LaunchAgent** is a user-level plist file that tells launchd to run
something on a schedule.

File location: `~/Library/LaunchAgents/com.newsdigest.daily.plist`

### 4.2  The Plist

```xml
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.newsdigest.daily</string>

    <key>ProgramArguments</key>
    <array>
        <string>/path/to/venv/bin/python3</string>
        <string>/path/to/main.py</string>
    </array>

    <key>WorkingDirectory</key>
    <string>/path/to/project</string>

    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>8</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>

    <key>StandardOutPath</key>
    <string>/path/to/logs/stdout.log</string>
</dict>
</plist>
```

Key decisions:
- `ProgramArguments` uses the **venv Python** — not the system Python,
  not `python3` on PATH.  This makes the schedule immune to PATH changes.
- `WorkingDirectory` ensures `main.py` can find `.env` and `.last_sent`
- `StartCalendarInterval` fires once daily at the specified time
- If the Mac was asleep at the scheduled time, macOS runs it on next wake

### 4.3  Install/Uninstall

```python
def _macos_install(hour: int, minute: int) -> None:
    # Unload existing schedule (if any)
    subprocess.run(["launchctl", "unload", str(plist_path)], ...)
    # Write new plist
    plist_path.write_text(plist_content)
    # Load into launchd
    subprocess.run(["launchctl", "load", str(plist_path)], ...)
```

The unload-write-load pattern ensures a clean update if the user changes
the schedule time.

---

## 5  Linux — cron

### 5.1  What is cron?

`cron` is the Unix scheduler daemon.  Each user has a `crontab` — a list
of scheduled commands.  The format:

```
minute hour day-of-month month day-of-week command
```

### 5.2  Our Cron Entry

```
0 8 * * * cd /path/to/project && /path/to/venv/bin/python3 /path/to/main.py >> logs/stdout.log 2>> logs/stderr.log # com.newsdigest.daily
```

Breakdown:
- `0 8 * * *` — at 08:00 every day
- `cd` to project — ensures correct working directory
- `>>` appends stdout, `2>>` appends stderr to log files
- `# com.newsdigest.daily` — comment tag for identification

### 5.3  Finding Our Entry

```python
CRON_TAG = f"# {SCHEDULE_LABEL}"
```

To update or remove, we filter crontab lines by this tag comment.
Lines containing `CRON_TAG` are ours; everything else is untouched.

### 5.4  Shell Quoting

```python
quoted_project_root = shlex.quote(str(PROJECT_ROOT))
```

`shlex.quote()` wraps paths in single quotes and escapes special
characters.  This handles spaces in paths (e.g., `/Users/John Smith/`).

---

## 6  Windows — Task Scheduler

### 6.1  schtasks.exe

Windows doesn't have cron.  Instead, it has **Task Scheduler**, accessible
via the `schtasks.exe` command-line tool.

```python
subprocess.run([
    "schtasks", "/Create",
    "/TN", SCHEDULE_LABEL,         # Task Name
    "/TR", f'"{VENV_PYTHON}" "{MAIN_PY}"',  # Task Run
    "/SC", "DAILY",                 # Schedule: daily
    "/ST", time_str,                # Start Time: HH:MM
    "/F",                           # Force overwrite
], ...)
```

### 6.2  Why `/F`?

The `/F` flag forces creation even if a task with the same name exists.
Without it, `schtasks` would error on re-creates.

---

## 7  Public API

```python
def install_schedule(hour: int, minute: int) -> str:
def uninstall_schedule() -> str:
def is_schedule_installed() -> bool:
```

The public API is **OS-agnostic**.  Each function calls `detect_os()`
and dispatches to the appropriate platform function.

```python
def install_schedule(hour: int, minute: int) -> str:
    os_type = detect_os()
    if os_type == "macos":
        _macos_install(hour, minute)
        return f"macOS LaunchAgent installed -- runs daily at {hour:02d}:{minute:02d}"
    elif os_type == "linux":
        _linux_install(hour, minute)
        return f"Cron job installed -- runs daily at {hour:02d}:{minute:02d}"
    elif os_type == "windows":
        _windows_install(hour, minute)
        return f"Windows Scheduled Task installed -- runs daily at {hour:02d}:{minute:02d}"
    else:
        raise ValueError("Automatic scheduling is not supported on this OS.")
```

Return values are human-readable strings — displayed directly to the user.

---

## 8  Constants

```python
SCHEDULE_LABEL = "com.newsdigest.daily"
```

Used as:
- macOS plist filename and Label key
- Linux crontab comment tag
- Windows task name

One identifier across all platforms keeps things consistent.

---

## 9  Log Files

All three backends redirect output to `logs/stdout.log` and
`logs/stderr.log`.  The `logs/` directory is created during install:

```python
LOGS_DIR.mkdir(parents=True, exist_ok=True)
```

This is essential for debugging — scheduled tasks run without a terminal,
so you can't see their output.  The log files are the only visibility.

---

## 10  Key Takeaways

| Concept | Implementation |
|---------|---------------|
| OS dispatch | `detect_os()` + platform-specific install functions |
| Clean API | Three public functions hide all OS complexity |
| Path independence | Uses venv Python path, not PATH-dependent `python3` |
| User-level only | No root/sudo/admin required |
| Identifiable | `SCHEDULE_LABEL` marks our entries on every OS |
| Debuggable | Stdout/stderr redirected to `logs/` directory |
