# =============================================================================
# install.ps1 — One-Line Installer for News Digest (Windows)
# =============================================================================
#
# This script is designed to be run from PowerShell:
#   irm https://raw.githubusercontent.com/sudo-nickPinto/acm-email-automation/public_attempt/install.ps1 | iex
#
# What it does:
#   1. Downloads the project as a zip from GitHub (no git required)
#   2. Extracts it to ~/news-digest
#   3. Launches the setup wizard (start.sh via Git Bash, or Python directly)
#
# No git, no GitHub account, no coding knowledge required.
# =============================================================================

$ErrorActionPreference = "Stop"

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
$RepoUrl    = "https://github.com/sudo-nickPinto/acm-email-automation/archive/refs/heads/public_attempt.zip"
$InstallDir = Join-Path $HOME "news-digest"
$ZipFile    = Join-Path $env:TEMP "news-digest-download.zip"
$ExtractDir = Join-Path $env:TEMP "news-digest-extract"

# ---------------------------------------------------------------------------
# Banner
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "  ==========================================================" -ForegroundColor Cyan
Write-Host "    News Digest — Installer" -ForegroundColor White
Write-Host "  ==========================================================" -ForegroundColor Cyan
Write-Host ""

# ---------------------------------------------------------------------------
# Step 1: Check if already installed
# ---------------------------------------------------------------------------
if (Test-Path $InstallDir) {
    Write-Host "  WARNING: News Digest is already installed at $InstallDir" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  To reconfigure, run:"
    Write-Host "    cd $InstallDir" -ForegroundColor DarkGray
    Write-Host "    python start_wizard.py" -ForegroundColor DarkGray
    Write-Host ""
    $answer = Read-Host "  Reinstall from scratch? [y/n]"
    if ($answer -notmatch '^[Yy]') {
        Write-Host ""
        Write-Host "  Keeping existing installation." -ForegroundColor Green
        exit 0
    }
    Write-Host "  Removing old installation..." -ForegroundColor DarkGray
    Remove-Item -Recurse -Force $InstallDir
}

# ---------------------------------------------------------------------------
# Step 2: Download
# ---------------------------------------------------------------------------
Write-Host "  Downloading News Digest..." -ForegroundColor Cyan

# Clean up previous temp files
if (Test-Path $ZipFile)    { Remove-Item -Force $ZipFile }
if (Test-Path $ExtractDir) { Remove-Item -Recurse -Force $ExtractDir }

try {
    Invoke-WebRequest -Uri $RepoUrl -OutFile $ZipFile -UseBasicParsing
} catch {
    Write-Host "  Download failed. Check your internet connection." -ForegroundColor Red
    Write-Host "  Error: $_" -ForegroundColor DarkGray
    exit 1
}

Write-Host "  Downloaded." -ForegroundColor Green

# ---------------------------------------------------------------------------
# Step 3: Extract
# ---------------------------------------------------------------------------
Write-Host "  Installing to $InstallDir..." -ForegroundColor Cyan

try {
    Expand-Archive -Path $ZipFile -DestinationPath $ExtractDir -Force
} catch {
    Write-Host "  Extraction failed." -ForegroundColor Red
    exit 1
}

# GitHub zips extract into a folder named repo-branch
$ExtractedFolder = Get-ChildItem -Path $ExtractDir -Directory | Select-Object -First 1

if (-not $ExtractedFolder) {
    Write-Host "  Extraction failed — no folder found." -ForegroundColor Red
    exit 1
}

# Move to the install location
Move-Item -Path $ExtractedFolder.FullName -Destination $InstallDir

# Clean up temp files
Remove-Item -Force $ZipFile -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force $ExtractDir -ErrorAction SilentlyContinue

Write-Host "  Installed to $InstallDir" -ForegroundColor Green

# ---------------------------------------------------------------------------
# Step 4: Check for Python
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "  Checking for Python..." -ForegroundColor Cyan

$PythonCmd = $null
foreach ($cmd in @("python3", "python", "py")) {
    try {
        $version = & $cmd --version 2>&1
        if ($version -match "Python (\d+)\.(\d+)") {
            $major = [int]$Matches[1]
            $minor = [int]$Matches[2]
            if ($major -ge 3 -and $minor -ge 10) {
                $PythonCmd = $cmd
                Write-Host "  Found $version ($cmd)" -ForegroundColor Green
                break
            }
        }
    } catch {
        # Command not found, try next
    }
}

if (-not $PythonCmd) {
    Write-Host ""
    Write-Host "  Python 3.10+ is not installed." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  To install Python:" -ForegroundColor White
    Write-Host "    1. Open: https://www.python.org/downloads/" -ForegroundColor White
    Write-Host "    2. Click the big yellow 'Download Python' button" -ForegroundColor White
    Write-Host "    3. Run the installer" -ForegroundColor White
    Write-Host "    4. IMPORTANT: Check 'Add Python to PATH' at the bottom!" -ForegroundColor Red
    Write-Host "    5. Click 'Install Now'" -ForegroundColor White
    Write-Host "    6. Close and reopen PowerShell" -ForegroundColor White
    Write-Host "    7. Run this installer again" -ForegroundColor White
    Write-Host ""
    Write-Host "  Or install via winget:" -ForegroundColor DarkGray
    Write-Host "    winget install Python.Python.3.12" -ForegroundColor DarkGray
    Write-Host ""
    exit 1
}

# ---------------------------------------------------------------------------
# Step 5: Create venv and install dependencies
# ---------------------------------------------------------------------------
Write-Host "  Setting up Python environment..." -ForegroundColor Cyan

Set-Location $InstallDir

& $PythonCmd -m venv venv

$VenvPython = Join-Path $InstallDir "venv\Scripts\python.exe"
$VenvPip    = Join-Path $InstallDir "venv\Scripts\pip.exe"

& $VenvPip install --quiet --upgrade pip 2>$null
& $VenvPip install --quiet -r (Join-Path $InstallDir "requirements.txt")

Write-Host "  All packages installed." -ForegroundColor Green

# ---------------------------------------------------------------------------
# Step 6: Launch the setup wizard
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "  Launching setup wizard..." -ForegroundColor White
Write-Host ""

& $VenvPython (Join-Path $InstallDir "setup_wizard.py")
