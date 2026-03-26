# =============================================================================
# news-digest.ps1 — PowerShell CLI wrapper for News Digest
# =============================================================================

$ErrorActionPreference = "Stop"

$InstallDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvPython = Join-Path $InstallDir "venv\Scripts\python.exe"
$MainPy = Join-Path $InstallDir "main.py"
$SetupWizard = Join-Path $InstallDir "setup_wizard.py"
$WrapperBinDir = Join-Path $HOME "AppData\Local\NewsDigest\bin"
$WrapperCmd = Join-Path $WrapperBinDir "news-digest.cmd"

function Show-Help {
    Write-Host ""
    Write-Host "  News Digest — Windows Command" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Usage:"
    Write-Host "    news-digest              Launch interactive menu"
    Write-Host "    news-digest run          Send today's digest"
    Write-Host "    news-digest run --dry    Preview without sending"
    Write-Host "    news-digest run --force  Force re-send even if already sent"
    Write-Host "    news-digest setup        Re-run the setup wizard"
    Write-Host "    news-digest status       Show current configuration"
    Write-Host "    news-digest uninstall    Remove everything"
    Write-Host "    news-digest help         Show this help message"
    Write-Host ""
}

function Assert-InstallReady {
    if (-not (Test-Path $InstallDir)) {
        Write-Host "  News Digest is not installed." -ForegroundColor Red
        exit 1
    }
    if (-not (Test-Path $VenvPython)) {
        Write-Host "  Installation is incomplete (no Python environment)." -ForegroundColor Red
        Write-Host "  Re-run: .\venv\Scripts\python.exe .\setup_wizard.py" -ForegroundColor DarkGray
        exit 1
    }
}

function Invoke-NewsDigestPython {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    & $VenvPython @Arguments
    exit $LASTEXITCODE
}

function Invoke-Status {
    & $VenvPython -c "from newsdigest.cli import action_status; action_status()"
    exit $LASTEXITCODE
}

function Invoke-Uninstall {
    Assert-InstallReady

    Write-Host ""
    Write-Host "  WARNING: This action cannot be undone." -ForegroundColor Yellow
    Write-Host "  It will remove the install directory, schedule, and Windows command wrapper."
    Write-Host ""

    $answer = Read-Host "  Type 'yes' to confirm"
    if ($answer -notmatch '^(?i:yes|y)$') {
        Write-Host "  Cancelled." -ForegroundColor Green
        exit 0
    }

    try {
        & $VenvPython -c "from newsdigest.scheduler import uninstall_schedule; print(uninstall_schedule())"
    } catch {
        Write-Host "  Schedule uninstall reported an error; continuing cleanup." -ForegroundColor Yellow
    }

    if (Test-Path $WrapperCmd) {
        Remove-Item -Force $WrapperCmd -ErrorAction SilentlyContinue
    }

    Remove-Item -Recurse -Force $InstallDir
    Write-Host "  News Digest has been removed." -ForegroundColor Green
    exit 0
}

Assert-InstallReady

$command = if ($args.Length -gt 0) { $args[0].ToLower() } else { "" }

switch ($command) {
    "" {
        Invoke-NewsDigestPython -Arguments @("-m", "newsdigest.cli")
    }
    "help" {
        Show-Help
        exit 0
    }
    "run" {
        if ($args.Length -gt 2) {
            Show-Help
            exit 1
        }

        $extra = @()
        if ($args.Length -eq 2) {
            switch ($args[1]) {
                "--dry" { $extra = @("--dry-run") }
                "--dry-run" { $extra = @("--dry-run") }
                "--force" { $extra = @("--force") }
                default {
                    Write-Host "  Unknown flag: $($args[1])" -ForegroundColor Red
                    Show-Help
                    exit 1
                }
            }
        }

        Invoke-NewsDigestPython -Arguments @($MainPy) + $extra
    }
    "setup" {
        Invoke-NewsDigestPython -Arguments @($SetupWizard)
    }
    "status" {
        Invoke-Status
    }
    "uninstall" {
        Invoke-Uninstall
    }
    default {
        Write-Host "  Unknown command: $command" -ForegroundColor Red
        Show-Help
        exit 1
    }
}
