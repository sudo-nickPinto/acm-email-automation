"""
Smoke tests for install.sh using local file:// release assets.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(
    sys.platform == "win32",
    reason="install.sh requires bash, only runs on Unix",
)

REPO_ROOT = Path(__file__).resolve().parent.parent
INSTALL_SCRIPT = REPO_ROOT / "install.sh"


def _write_release_assets(
    base_dir: Path,
    *,
    checksum_match: bool = True,
    checksum_entry: bool = True,
    top_level_dir: bool = True,
    root_dir_name: str = "news-digest",
) -> tuple[Path, Path]:
    package_path = base_dir / "news-digest.zip"
    checksum_path = base_dir / "SHA256SUMS.txt"

    with zipfile.ZipFile(package_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        if top_level_dir:
            archive.writestr(f"{root_dir_name}/start.sh", "#!/bin/bash\necho setup\n")
            archive.writestr(f"{root_dir_name}/news-digest", "#!/bin/bash\necho cli\n")
            archive.writestr(f"{root_dir_name}/setup_wizard.py", "print('wizard')\n")
            archive.writestr(f"{root_dir_name}/README.md", "hello\n")
        else:
            archive.writestr("README.md", "broken\n")

    digest = hashlib.sha256(package_path.read_bytes()).hexdigest()
    if not checksum_match:
        digest = "0" * 64
    if checksum_entry:
        checksum_path.write_text(f"{digest}  news-digest.zip\n")
    else:
        checksum_path.write_text(f"{digest}  something-else.zip\n")

    return package_path, checksum_path


def _run_installer(tmp_path: Path, package_path: Path, checksum_path: Path) -> subprocess.CompletedProcess[str]:
    home_dir = tmp_path / "home"
    home_dir.mkdir()
    install_dir = tmp_path / "installed-news-digest"
    bin_dir = tmp_path / "bin"

    env = os.environ.copy()
    env.update({
        "HOME": str(home_dir),
        "NEWSDIGEST_PACKAGE_URL": package_path.as_uri(),
        "NEWSDIGEST_CHECKSUM_URL": checksum_path.as_uri(),
        "NEWSDIGEST_INSTALL_DIR": str(install_dir),
        "NEWSDIGEST_BIN_DIR": str(bin_dir),
        "NEWSDIGEST_SKIP_LAUNCH": "1",
    })

    return subprocess.run(
        ["bash", str(INSTALL_SCRIPT)],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
    )


class TestInstallSh:

    def test_installs_from_local_release_assets(self, tmp_path):
        release_dir = tmp_path / "release"
        release_dir.mkdir()
        package_path, checksum_path = _write_release_assets(release_dir)

        result = _run_installer(tmp_path, package_path, checksum_path)

        assert result.returncode == 0
        install_dir = tmp_path / "installed-news-digest"
        assert (install_dir / "start.sh").exists()
        assert (install_dir / "news-digest").exists()
        assert (tmp_path / "bin" / "news-digest").is_symlink()
        assert "Downloaded and verified" in result.stdout
        assert "Skipping setup wizard launch" in result.stdout

    def test_fails_on_checksum_mismatch(self, tmp_path):
        release_dir = tmp_path / "release"
        release_dir.mkdir()
        package_path, checksum_path = _write_release_assets(release_dir, checksum_match=False)

        result = _run_installer(tmp_path, package_path, checksum_path)

        assert result.returncode != 0
        assert "Checksum verification failed" in result.stdout

    def test_fails_when_checksum_entry_is_missing(self, tmp_path):
        release_dir = tmp_path / "release"
        release_dir.mkdir()
        package_path, checksum_path = _write_release_assets(release_dir, checksum_entry=False)

        result = _run_installer(tmp_path, package_path, checksum_path)

        assert result.returncode != 0
        assert "valid checksum for news-digest.zip" in result.stdout

    def test_fails_when_archive_has_no_top_level_directory(self, tmp_path):
        release_dir = tmp_path / "release"
        release_dir.mkdir()
        package_path, checksum_path = _write_release_assets(release_dir, top_level_dir=False)

        result = _run_installer(tmp_path, package_path, checksum_path)

        assert result.returncode != 0
        assert "expected a single top-level news-digest/ folder" in result.stdout

    def test_fails_when_archive_root_name_is_unexpected(self, tmp_path):
        release_dir = tmp_path / "release"
        release_dir.mkdir()
        package_path, checksum_path = _write_release_assets(release_dir, root_dir_name="unexpected-root")

        result = _run_installer(tmp_path, package_path, checksum_path)

        assert result.returncode != 0
        assert "package root must be news-digest/" in result.stdout
