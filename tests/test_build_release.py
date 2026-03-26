"""
Tests for scripts.build_release.
"""

from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import scripts.build_release as build_release


class TestShouldPackage:

    def test_excludes_expected_repo_only_paths(self):
        assert build_release.should_package(Path("tests/test_main.py")) is False
        assert build_release.should_package(Path("scripts/build_release.py")) is False
        assert build_release.should_package(Path("dist/news-digest.zip")) is False
        assert build_release.should_package(Path("education/README.md")) is False
        assert build_release.should_package(Path(".gitignore")) is False
        assert build_release.should_package(Path("install.sh")) is False

    def test_keeps_runtime_files(self):
        assert build_release.should_package(Path("README.md")) is True
        assert build_release.should_package(Path("main.py")) is True
        assert build_release.should_package(Path("newsdigest/emailer.py")) is True


class TestTrackedFiles:

    @patch("scripts.build_release.subprocess.run")
    def test_tracked_files_filters_git_output(self, mock_run):
        mock_run.return_value = MagicMock(
            stdout=b"README.md\0tests/test_main.py\0education/README.md\0newsdigest/emailer.py\0"
        )

        with patch.object(build_release, "PROJECT_ROOT", Path("/tmp/project")):
            files = build_release.tracked_files()

        assert files == [Path("README.md"), Path("newsdigest/emailer.py")]


class TestEnsureCleanWorktree:

    @patch.dict("os.environ", {}, clear=True)
    @patch("scripts.build_release.subprocess.run")
    def test_exits_when_worktree_is_dirty(self, mock_run):
        mock_run.return_value = MagicMock(stdout=" M README.md\n")

        with patch.object(build_release, "PROJECT_ROOT", Path("/tmp/project")):
            try:
                build_release.ensure_clean_worktree()
            except SystemExit as exc:
                assert "dirty worktree" in str(exc)
            else:
                raise AssertionError("ensure_clean_worktree() should exit on dirty trees")

    @patch.dict("os.environ", {"NEWSDIGEST_ALLOW_DIRTY": "1"}, clear=True)
    @patch("scripts.build_release.subprocess.run")
    def test_allows_dirty_worktree_when_override_is_set(self, mock_run):
        build_release.ensure_clean_worktree()

        mock_run.assert_not_called()


class TestBuildReleaseArtifacts:

    def test_main_builds_expected_release_artifacts(self, tmp_path):
        project_root = tmp_path / "repo"
        project_root.mkdir()
        dist_dir = project_root / "dist"

        (project_root / "README.md").write_text("hello\n")
        (project_root / "main.py").write_text("print('hi')\n")
        (project_root / "requirements.lock").write_text("requests==2.33.0\n")
        (project_root / "install.sh").write_text("#!/bin/bash\n")
        (project_root / "install.ps1").write_text("Write-Host 'hi'\n")
        newsdigest_dir = project_root / "newsdigest"
        newsdigest_dir.mkdir()
        (newsdigest_dir / "__init__.py").write_text("")

        with patch.object(build_release, "PROJECT_ROOT", project_root), \
                patch.object(build_release, "DIST_DIR", dist_dir), \
                patch.object(build_release, "ensure_clean_worktree"), \
                patch.object(build_release, "tracked_files", return_value=[
                    Path("README.md"),
                    Path("main.py"),
                    Path("newsdigest/__init__.py"),
                    Path("requirements.lock"),
                ]):
            result = build_release.main()

        assert result == 0
        assert sorted(path.name for path in dist_dir.iterdir()) == [
            "SHA256SUMS.txt",
            "SHARE_THIS.txt",
            "install.ps1",
            "install.sh",
            "news-digest.zip",
        ]

        archive_path = dist_dir / "news-digest.zip"
        checksums = {
            line.split()[1]: line.split()[0]
            for line in (dist_dir / "SHA256SUMS.txt").read_text().strip().splitlines()
        }
        expected_hash = hashlib.sha256(archive_path.read_bytes()).hexdigest()
        assert checksums == {
            "install.ps1": hashlib.sha256((dist_dir / "install.ps1").read_bytes()).hexdigest(),
            "install.sh": hashlib.sha256((dist_dir / "install.sh").read_bytes()).hexdigest(),
            "news-digest.zip": expected_hash,
        }

        share_text = (dist_dir / "SHARE_THIS.txt").read_text()
        assert "curl -fsSLO" in share_text
        assert "powershell -ExecutionPolicy Bypass -File" in share_text
        assert "Fast-path alternatives" in share_text

        with zipfile.ZipFile(archive_path) as archive:
            names = sorted(archive.namelist())
        assert names == [
            "news-digest/README.md",
            "news-digest/main.py",
            "news-digest/newsdigest/__init__.py",
            "news-digest/requirements.lock",
        ]
