#!/usr/bin/env python3
"""
Build the GitHub Release assets used by the public installer flow.

Outputs:
  dist/news-digest.zip
  dist/SHA256SUMS.txt
  dist/install.sh
  dist/install.ps1
  dist/SHARE_THIS.txt
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import zipfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DIST_DIR = PROJECT_ROOT / "dist"
PACKAGE_NAME = "news-digest.zip"
CHECKSUM_NAME = "SHA256SUMS.txt"
SHARE_FILE_NAME = "SHARE_THIS.txt"
ZIP_ROOT = Path("news-digest")
INSTALLER_NAMES = ("install.sh", "install.ps1")
EXCLUDED_PREFIXES = (
    ".github/",
    "dist/",
    "education/",
    "scripts/",
    "tests/",
)
EXCLUDED_FILES = {
    ".gitignore",
    "install.sh",
    "install.ps1",
}
MANDATORY_PACKAGE_FILES = (
    Path("news-digest.ps1"),
    Path("requirements.lock"),
    Path("newsdigest/paths.py"),
)


def ensure_clean_worktree() -> None:
    if os.environ.get("NEWSDIGEST_ALLOW_DIRTY") == "1":
        return

    try:
        result = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=no"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        raise SystemExit("git is required to build release assets.")
    except subprocess.CalledProcessError as exc:
        raise SystemExit(exc.stderr.strip() or "git status failed.")

    if result.stdout.strip():
        raise SystemExit(
            "Refusing to build from a dirty worktree. Commit/stash your changes first, "
            "or set NEWSDIGEST_ALLOW_DIRTY=1 for an intentional local smoke build."
        )


def tracked_files() -> list[Path]:
    try:
        result = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=False,
        )
    except FileNotFoundError:
        raise SystemExit("git is required to build release assets.")
    except subprocess.CalledProcessError as exc:
        raise SystemExit(exc.stderr.decode().strip() or "git ls-files failed.")

    files = {
        Path(raw.decode("utf-8"))
        for raw in result.stdout.split(b"\0")
        if raw
    }
    for rel_path in MANDATORY_PACKAGE_FILES:
        if (PROJECT_ROOT / rel_path).exists():
            files.add(rel_path)
    return sorted(path for path in files if should_package(path))


def should_package(path: Path) -> bool:
    rel = path.as_posix()
    if rel in EXCLUDED_FILES:
        return False
    return not any(rel.startswith(prefix) for prefix in EXCLUDED_PREFIXES)


def build_zip(files: list[Path]) -> Path:
    archive_path = DIST_DIR / PACKAGE_NAME
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for rel_path in files:
            archive.write(PROJECT_ROOT / rel_path, arcname=str(ZIP_ROOT / rel_path))
    return archive_path


def write_checksums(paths: list[Path]) -> None:
    lines = []
    for path in paths:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f"{digest}  {path.name}")
    (DIST_DIR / CHECKSUM_NAME).write_text("\n".join(lines) + "\n")


def copy_installers() -> None:
    for name in INSTALLER_NAMES:
        shutil.copy2(PROJECT_ROOT / name, DIST_DIR / name)


def write_share_file() -> None:
    content = """Upload these files to a GitHub Release:
- install.sh
- install.ps1
- news-digest.zip
- SHA256SUMS.txt

Recommended install commands for friends:

macOS / Linux
curl -fsSLO https://github.com/sudo-nickPinto/acm-email-automation/releases/latest/download/install.sh
bash install.sh

Windows (PowerShell)
iwr https://github.com/sudo-nickPinto/acm-email-automation/releases/latest/download/install.ps1 -OutFile install.ps1
powershell -ExecutionPolicy Bypass -File .\\install.ps1

Fast-path alternatives (runs remote script immediately):
- macOS / Linux: curl -fsSL https://github.com/sudo-nickPinto/acm-email-automation/releases/latest/download/install.sh | bash
- Windows (PowerShell): irm https://github.com/sudo-nickPinto/acm-email-automation/releases/latest/download/install.ps1 | iex
"""
    (DIST_DIR / SHARE_FILE_NAME).write_text(content)


def main() -> int:
    ensure_clean_worktree()

    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True)

    files = tracked_files()
    archive_path = build_zip(files)
    copy_installers()
    write_checksums([archive_path, *(DIST_DIR / name for name in INSTALLER_NAMES)])
    write_share_file()

    print(f"Built release assets in {DIST_DIR}")
    print(f"- {PACKAGE_NAME}")
    print(f"- {CHECKSUM_NAME}")
    print("- install.sh")
    print("- install.ps1")
    print(f"- {SHARE_FILE_NAME}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
