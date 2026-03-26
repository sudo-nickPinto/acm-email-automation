# =============================================================================
# install.ps1 — One-Line Installer for News Digest (Windows)
# =============================================================================
#
# This script can be downloaded from a GitHub Release asset and run locally:
#   iwr https://github.com/sudo-nickPinto/acm-email-automation/releases/latest/download/install.ps1 -OutFile install.ps1
#   powershell -ExecutionPolicy Bypass -File .\install.ps1
#
# Convenience-only shortcut:
#   irm https://github.com/sudo-nickPinto/acm-email-automation/releases/latest/download/install.ps1 | iex
#
# What it does:
#   1. Downloads the packaged app zip from the latest GitHub Release
#   2. Verifies the download against SHA256SUMS.txt
#   3. Extracts it to ~/news-digest
#   4. Launches the setup wizard
# =============================================================================

$ErrorActionPreference = "Stop"

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
$ReleaseBaseUrl = if ($env:NEWSDIGEST_RELEASE_BASE_URL) {
    $env:NEWSDIGEST_RELEASE_BASE_URL
} else {
    "https://github.com/sudo-nickPinto/acm-email-automation/releases/latest/download"
}
$PackageUrl = if ($env:NEWSDIGEST_PACKAGE_URL) {
    $env:NEWSDIGEST_PACKAGE_URL
} else {
    "$ReleaseBaseUrl/news-digest.zip"
}
$ChecksumUrl = if ($env:NEWSDIGEST_CHECKSUM_URL) {
    $env:NEWSDIGEST_CHECKSUM_URL
} else {
    "$ReleaseBaseUrl/SHA256SUMS.txt"
}
$InstallDir = if ($env:NEWSDIGEST_INSTALL_DIR) {
    $env:NEWSDIGEST_INSTALL_DIR
} else {
    Join-Path $HOME "news-digest"
}
$SkipLaunch = $env:NEWSDIGEST_SKIP_LAUNCH -eq "1"
$TempBase = if ($env:TEMP) { $env:TEMP } else { [System.IO.Path]::GetTempPath() }
$TempRoot = Join-Path $TempBase ("news-digest-install-" + [System.Guid]::NewGuid().ToString("N"))
$ZipFile = Join-Path $TempRoot "news-digest-download.zip"
$ChecksumFile = Join-Path $TempRoot "SHA256SUMS.txt"
$ExtractDir = Join-Path $TempRoot "extracted"

function Cleanup-Temp {
    if (Test-Path $TempRoot) {
        Remove-Item -Recurse -Force $TempRoot -ErrorAction SilentlyContinue
    }
}

function Assert-LastExitCode {
    param([string]$Step)

    if ($LASTEXITCODE -ne 0) {
        Write-Host "  $Step failed." -ForegroundColor Red
        Write-Host "  Exit code: $LASTEXITCODE" -ForegroundColor DarkGray
        exit $LASTEXITCODE
    }
}

function Install-CommandWrapper {
    $BinDir = Join-Path $HOME "AppData\Local\NewsDigest\bin"
    $WrapperPath = Join-Path $BinDir "news-digest.cmd"
    $LauncherPath = Join-Path $InstallDir "news-digest.ps1"
    $PowerShellExe = if ($env:SystemRoot) {
        Join-Path $env:SystemRoot "System32\WindowsPowerShell\v1.0\powershell.exe"
    } else {
        "pwsh"
    }

    New-Item -ItemType Directory -Path $BinDir -Force | Out-Null

    $wrapperContent = @(
        "@echo off",
        "`"$PowerShellExe`" -NoProfile -ExecutionPolicy Bypass -File `"$LauncherPath`" %*"
    ) -join "`r`n"
    Set-Content -Path $WrapperPath -Value $wrapperContent -Encoding ASCII

    if ($IsWindows) {
        $currentUserPath = [Environment]::GetEnvironmentVariable("Path", "User")
        $pathEntries = @()
        if ($currentUserPath) {
            $pathEntries = $currentUserPath -split ';' | Where-Object { $_ }
        }

        if ($pathEntries -notcontains $BinDir) {
            $newUserPath = if ($currentUserPath) { "$currentUserPath;$BinDir" } else { $BinDir }
            [Environment]::SetEnvironmentVariable("Path", $newUserPath, "User")
        }
    }

    if (-not (($env:Path -split [System.IO.Path]::PathSeparator) -contains $BinDir)) {
        $env:Path = "$BinDir$([System.IO.Path]::PathSeparator)$env:Path"
    }

    Write-Host "  Installed news-digest command to $BinDir" -ForegroundColor Green
}

New-Item -ItemType Directory -Path $TempRoot -Force | Out-Null

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
    Write-Host "    .\\venv\\Scripts\\python.exe .\\setup_wizard.py" -ForegroundColor DarkGray
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
# Step 2: Download + verify
# ---------------------------------------------------------------------------
Write-Host "  Downloading News Digest..." -ForegroundColor Cyan

try {
    Invoke-WebRequest -Uri $PackageUrl -OutFile $ZipFile -UseBasicParsing
} catch {
    Write-Host "  Download failed." -ForegroundColor Red
    Write-Host "  If you're the maintainer, upload dist/news-digest.zip to the latest GitHub Release." -ForegroundColor DarkGray
    Cleanup-Temp
    exit 1
}

try {
    Invoke-WebRequest -Uri $ChecksumUrl -OutFile $ChecksumFile -UseBasicParsing
} catch {
    Write-Host "  Could not download SHA256SUMS.txt." -ForegroundColor Red
    Write-Host "  If you're the maintainer, upload dist/SHA256SUMS.txt to the latest GitHub Release." -ForegroundColor DarkGray
    Cleanup-Temp
    exit 1
}

$checksumMatch = Select-String -Path $ChecksumFile -Pattern '^(?<hash>[A-Fa-f0-9]{64})\s+\*?news-digest\.zip$' | Select-Object -First 1

if (-not $checksumMatch) {
    Write-Host "  SHA256SUMS.txt does not contain a valid checksum for news-digest.zip." -ForegroundColor Red
    Cleanup-Temp
    exit 1
}

$ExpectedHash = $checksumMatch.Matches[0].Groups["hash"].Value.ToLower()
$ActualHash = (Get-FileHash -Path $ZipFile -Algorithm SHA256).Hash.ToLower()

if ($ExpectedHash -ne $ActualHash) {
    Write-Host "  Checksum verification failed." -ForegroundColor Red
    Write-Host "  Expected: $ExpectedHash" -ForegroundColor DarkGray
    Write-Host "  Actual:   $ActualHash" -ForegroundColor DarkGray
    Cleanup-Temp
    exit 1
}

Write-Host "  Downloaded and verified." -ForegroundColor Green

# ---------------------------------------------------------------------------
# Step 3: Extract
# ---------------------------------------------------------------------------
Write-Host "  Installing to $InstallDir..." -ForegroundColor Cyan

try {
    Expand-Archive -Path $ZipFile -DestinationPath $ExtractDir -Force
} catch {
    Write-Host "  Extraction failed." -ForegroundColor Red
    Cleanup-Temp
    exit 1
}

$TopLevelEntries = @(Get-ChildItem -Path $ExtractDir -Force)
$TopLevelDirs = @(Get-ChildItem -Path $ExtractDir -Directory -Force)

if ($TopLevelEntries.Count -ne 1 -or $TopLevelDirs.Count -ne 1) {
    Write-Host "  Extraction failed — expected a single top-level news-digest/ folder." -ForegroundColor Red
    Cleanup-Temp
    exit 1
}

$ExtractedFolder = $TopLevelDirs[0]

if ($ExtractedFolder.Name -ne "news-digest") {
    Write-Host "  Extraction failed — package root must be news-digest/." -ForegroundColor Red
    Cleanup-Temp
    exit 1
}

foreach ($requiredPath in @("start.sh", "news-digest", "news-digest.ps1", "setup_wizard.py")) {
    if (-not (Test-Path (Join-Path $ExtractedFolder.FullName $requiredPath))) {
        Write-Host "  Extraction failed — package is missing $requiredPath." -ForegroundColor Red
        Cleanup-Temp
        exit 1
    }
}

try {
    Move-Item -Path $ExtractedFolder.FullName -Destination $InstallDir
} catch {
    Write-Host "  Could not move the extracted files into place." -ForegroundColor Red
    Cleanup-Temp
    exit 1
}
Cleanup-Temp

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
            if ($major -gt 3 -or ($major -eq 3 -and $minor -ge 10)) {
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
Assert-LastExitCode "Virtual environment creation"

$VenvPython = Join-Path $InstallDir "venv\Scripts\python.exe"
$VenvPip = Join-Path $InstallDir "venv\Scripts\pip.exe"
$RequirementsFile = Join-Path $InstallDir "requirements.lock"
if (-not (Test-Path $RequirementsFile)) {
    $RequirementsFile = Join-Path $InstallDir "requirements.txt"
}

if (-not (Test-Path $VenvPython) -or -not (Test-Path $VenvPip)) {
    Write-Host "  Virtual environment layout is incomplete." -ForegroundColor Red
    Write-Host "  Expected $VenvPython and $VenvPip" -ForegroundColor DarkGray
    exit 1
}

& $VenvPip install --quiet --upgrade pip 2>$null
Assert-LastExitCode "pip upgrade"
& $VenvPip install --quiet -r $RequirementsFile
Assert-LastExitCode "Dependency installation"

Write-Host "  All packages installed." -ForegroundColor Green

Install-CommandWrapper

# ---------------------------------------------------------------------------
# Step 6: Launch the setup wizard
# ---------------------------------------------------------------------------
if ($SkipLaunch) {
    Write-Host ""
    Write-Host "  Skipping setup wizard launch (NEWSDIGEST_SKIP_LAUNCH=1)." -ForegroundColor DarkGray
    exit 0
}

Write-Host ""
Write-Host "  Launching setup wizard..." -ForegroundColor White
Write-Host ""

& $VenvPython (Join-Path $InstallDir "setup_wizard.py")
Assert-LastExitCode "Setup wizard launch"
