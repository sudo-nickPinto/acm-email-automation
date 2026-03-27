"""
Smoke tests for install.ps1 using local file:// release assets and PowerShell.
"""

from __future__ import annotations

import hashlib
import http.server
import os
import shutil
import socketserver
import subprocess
import sys
import threading
import zipfile
from functools import partial
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent
INSTALL_SCRIPT = REPO_ROOT / "install.ps1"
PWSH = shutil.which("pwsh")


def _write_release_assets(base_dir: Path) -> tuple[Path, Path]:
    package_path = base_dir / "news-digest.zip"
    checksum_path = base_dir / "SHA256SUMS.txt"

    with zipfile.ZipFile(package_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("news-digest/start.sh", "#!/bin/bash\necho setup\n")
        archive.writestr("news-digest/news-digest", "#!/bin/bash\necho cli\n")
        archive.writestr("news-digest/news-digest.ps1", "Write-Host 'launcher'\n")
        archive.writestr("news-digest/setup_wizard.py", "print('wizard')\n")
        archive.writestr("news-digest/requirements.lock", "\n")
        archive.writestr("news-digest/requirements.txt", "\n")

    digest = hashlib.sha256(package_path.read_bytes()).hexdigest()
    checksum_path.write_text(f"{digest}  news-digest.zip\n")
    return package_path, checksum_path


def _write_python_shims(base_dir: Path) -> Path:
    shim_dir = base_dir / "shims"
    shim_dir.mkdir()

    python_shim = shim_dir / "python3"
    python_shim.write_text(
        "#!/bin/sh\n"
        "if [ \"$1\" = \"--version\" ]; then\n"
        "  echo 'Python 3.13.0'\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"$1\" = \"-m\" ] && [ \"$2\" = \"venv\" ] && [ \"$3\" = \"venv\" ]; then\n"
        "  mkdir -p venv/Scripts\n"
        "  cat > venv/Scripts/python.exe <<'EOF'\n"
        "#!/bin/sh\n"
        "exit 0\n"
        "EOF\n"
        "  cat > venv/Scripts/pip.exe <<'EOF'\n"
        "#!/bin/sh\n"
        "exit 0\n"
        "EOF\n"
        "  chmod +x venv/Scripts/python.exe venv/Scripts/pip.exe\n"
        "  exit 0\n"
        "fi\n"
        "exit 0\n"
    )
    if sys.platform != "win32":
        python_shim.chmod(0o755)
        (shim_dir / "python").symlink_to(python_shim.name)
        (shim_dir / "py").symlink_to(python_shim.name)
    return shim_dir


class _ThreadingTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True


def _serve_directory(directory: Path):
    handler = partial(http.server.SimpleHTTPRequestHandler, directory=str(directory))
    server = _ThreadingTCPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


@pytest.mark.skipif(PWSH is None, reason="pwsh is required for install.ps1 smoke tests")
def test_install_ps1_installs_from_local_release_assets(tmp_path):
    release_dir = tmp_path / "release"
    release_dir.mkdir()
    package_path, checksum_path = _write_release_assets(release_dir)
    shim_dir = _write_python_shims(tmp_path)
    server, thread = _serve_directory(release_dir)

    home_dir = tmp_path / "home"
    home_dir.mkdir()
    install_dir = tmp_path / "installed-news-digest"
    temp_dir = tmp_path / "temp"
    temp_dir.mkdir()
    base_url = f"http://127.0.0.1:{server.server_address[1]}"

    env = os.environ.copy()
    env.update({
        "HOME": str(home_dir),
        "TEMP": str(temp_dir),
        "PATH": f"{shim_dir}:{env['PATH']}",
        "NEWSDIGEST_PACKAGE_URL": f"{base_url}/{package_path.name}",
        "NEWSDIGEST_CHECKSUM_URL": f"{base_url}/{checksum_path.name}",
        "NEWSDIGEST_INSTALL_DIR": str(install_dir),
        "NEWSDIGEST_SKIP_LAUNCH": "1",
    })

    try:
        result = subprocess.run(
            [PWSH, "-NoProfile", "-File", str(INSTALL_SCRIPT)],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    assert result.returncode == 0, result.stdout + result.stderr
    assert (install_dir / "requirements.lock").exists()
    assert (install_dir / "venv" / "Scripts" / "python.exe").exists()
    assert (install_dir / "venv" / "Scripts" / "pip.exe").exists()
    assert (home_dir / "AppData" / "Local" / "NewsDigest" / "bin" / "news-digest.cmd").exists()
    assert "Downloaded and verified." in result.stdout
    assert "Installed news-digest command" in result.stdout
    assert "Skipping setup wizard launch" in result.stdout
