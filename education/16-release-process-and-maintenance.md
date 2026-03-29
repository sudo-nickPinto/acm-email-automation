# Lesson 16 — Release Process and Maintenance

> **Goal:** Understand how `scripts/build_release.py` packages the
> project for distribution, and how the release cycle works.

---

## 1  Release Artifacts

The build script produces five files in `dist/`:

| File | Purpose |
|------|---------|
| `news-digest.zip` | Complete project (minus dev files) |
| `SHA256SUMS.txt` | Integrity checksums for all artifacts |
| `install.sh` | macOS/Linux installer (standalone copy) |
| `install.ps1` | Windows installer (standalone copy) |
| `SHARE_THIS.txt` | Commands to share with friends |

---

## 2  Build Script Walkthrough

### 2.1  Clean Worktree Check

```python
def ensure_clean_worktree() -> None:
    result = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=no"], ...
    )
    if result.stdout.strip():
        raise SystemExit("Refusing to build from a dirty worktree.")
```

Prevents building with uncommitted changes.  The escape hatch
`NEWSDIGEST_ALLOW_DIRTY=1` is for CI smoke tests.

### 2.2  File Selection

```python
EXCLUDED_PREFIXES = (
    ".github/", "dist/", "education/", "scripts/", "tests/",
)
EXCLUDED_FILES = {".gitignore", "install.sh", "install.ps1"}

MANDATORY_PACKAGE_FILES = (
    Path("news-digest.ps1"),
    Path("requirements.lock"),
    Path("newsdigest/paths.py"),
)
```

Files are selected from `git ls-files` (tracked files only), then
filtered:
- **Excluded:** CI workflows, test suite, build scripts, education docs,
  installers (they're copied separately), `.gitignore`
- **Mandatory:** Files that must be in the zip even if not tracked yet

### 2.3  Zip Construction

```python
def build_zip(files: list[Path]) -> Path:
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for rel_path in files:
            archive.write(PROJECT_ROOT / rel_path, arcname=str(ZIP_ROOT / rel_path))
```

Files are placed under a `news-digest/` root in the zip, so extracting
creates a self-contained directory.

### 2.4  Checksum Generation

```python
def write_checksums(paths: list[Path]) -> None:
    for path in paths:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f"{digest}  {path.name}")
```

SHA-256 checksums in the standard `sha256sum` format (`hash  filename`).
Both installers parse this file to verify the zip.

---

## 3  Release Workflow

```
1. Make changes → commit → push
2. Run: python scripts/build_release.py
3. Upload dist/* to a GitHub Release
4. Friends run: curl -fsSL <url>/install.sh | bash
```

The `SHARE_THIS.txt` file contains copy-pasteable commands for sharing.

---

## 4  Version Control Strategy

| Branch | Purpose |
|--------|---------|
| `main` | Stable release branch |
| `public_attempt` | Active development |
| `secure-release-installer-hardening` | Security-focused feature branch |

Feature branches merge into `public_attempt`, which is periodically
merged into `main` for releases.

---

## 5  Key Takeaways

| Concept | Implementation |
|---------|---------------|
| Reproducible builds | Clean worktree check + git ls-files |
| Integrity | SHA-256 checksums for all artifacts |
| Minimal distribution | Dev files excluded from zip |
| Self-contained | Zip contains everything users need |
