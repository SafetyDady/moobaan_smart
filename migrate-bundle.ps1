# migrate-bundle.ps1 - Bundle local-only files (.env, .claude/) into a zip
# Usage:
#   .\migrate-bundle.ps1          # interactive (prompts if git is dirty)
#   .\migrate-bundle.ps1 -Force   # skip git checks
#
# Output: moobaan-smart-migration-YYYYMMDD.zip (~10 KB)
# Code itself lives on GitHub, so only personal/secret files need bundling.

param(
    [switch]$Force
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = $PSScriptRoot
$Timestamp = Get-Date -Format 'yyyyMMdd'
$BundleName = "moobaan-smart-migration-$Timestamp"
$BundleDir = Join-Path $env:TEMP $BundleName
$ZipPath = Join-Path $ProjectRoot ($BundleName + '.zip')

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host " Moobaan Smart - Migration Bundle Builder" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# ---------- 1. Pre-flight: git status ----------
Write-Host "[1/4] Checking git status..." -ForegroundColor Yellow
Push-Location $ProjectRoot
try {
    $gitStatus = git status --porcelain 2>$null
    if ($gitStatus) {
        Write-Host "  WARNING: uncommitted changes detected:" -ForegroundColor Red
        $gitStatus | ForEach-Object { Write-Host ("    " + $_) -ForegroundColor DarkYellow }
        Write-Host ""
        if ($Force) {
            Write-Host "  -Force flag set; continuing." -ForegroundColor Yellow
        } else {
            $choice = Read-Host "  Continue anyway? (y/N)"
            if ($choice -ne 'y' -and $choice -ne 'Y') {
                Write-Host "  Aborted. Commit + push first, then re-run." -ForegroundColor Red
                exit 1
            }
        }
    } else {
        Write-Host "  OK: working tree clean" -ForegroundColor Green
    }

    $unpushed = git log '@{u}..HEAD' --oneline 2>$null
    if ($unpushed) {
        Write-Host "  WARNING: commits not pushed yet:" -ForegroundColor Red
        $unpushed | ForEach-Object { Write-Host ("    " + $_) -ForegroundColor DarkYellow }
        Write-Host ""
        if ($Force) {
            Write-Host "  -Force flag set; continuing." -ForegroundColor Yellow
        } else {
            $choice = Read-Host "  Continue anyway? (y/N)"
            if ($choice -ne 'y' -and $choice -ne 'Y') {
                Write-Host "  Aborted. Run 'git push' first, then re-run." -ForegroundColor Red
                exit 1
            }
        }
    } else {
        Write-Host "  OK: synced with remote" -ForegroundColor Green
    }
} finally {
    Pop-Location
}

# ---------- 2. Stage files ----------
Write-Host ""
Write-Host "[2/4] Staging files..." -ForegroundColor Yellow
if (Test-Path $BundleDir) { Remove-Item -Recurse -Force $BundleDir }
New-Item -ItemType Directory -Path $BundleDir | Out-Null

$filesToBundle = @(
    @{ Source = 'backend\.env';                Required = $true  },
    @{ Source = 'frontend\.env';               Required = $true  },
    @{ Source = '.claude\settings.local.json'; Required = $false },
    @{ Source = 'MIGRATION.md';                Required = $true  }
)

foreach ($f in $filesToBundle) {
    $src = Join-Path $ProjectRoot $f.Source
    if (Test-Path $src) {
        $dst = Join-Path $BundleDir $f.Source
        $dstDir = Split-Path $dst -Parent
        if (-not (Test-Path $dstDir)) {
            New-Item -ItemType Directory -Path $dstDir -Force | Out-Null
        }
        Copy-Item $src $dst
        $size = (Get-Item $src).Length
        $line = "  ADD: " + $f.Source + " (" + $size + " B)"
        Write-Host $line -ForegroundColor Green
    } else {
        if ($f.Required) {
            $msg = "  MISSING: " + $f.Source + " (required)"
            Write-Host $msg -ForegroundColor Red
        } else {
            $msg = "  SKIP: " + $f.Source + " (not present)"
            Write-Host $msg -ForegroundColor DarkGray
        }
    }
}

# README inside the zip
$readmePath = Join-Path $BundleDir 'README-FIRST.txt'
$gitSha = ''
try { $gitSha = (git -C $ProjectRoot rev-parse HEAD).Substring(0,7) } catch { $gitSha = 'unknown' }
$dateStr = Get-Date -Format 'yyyy-MM-dd HH:mm'

$readmeLines = @()
$readmeLines += 'Moobaan Smart - Migration Bundle'
$readmeLines += '================================='
$readmeLines += ('Created: ' + $dateStr)
$readmeLines += ('Git commit: ' + $gitSha)
$readmeLines += 'Repo: https://github.com/SafetyDady/moobaan_smart'
$readmeLines += ''
$readmeLines += 'Steps on the new PC:'
$readmeLines += '  1. git clone https://github.com/SafetyDady/moobaan_smart.git C:\web_project\moobaan_smart'
$readmeLines += '  2. Extract this zip into C:\web_project\moobaan_smart\ (overwrite if asked)'
$readmeLines += '  3. cd backend ; python -m venv .venv ; .venv\Scripts\activate ; pip install -r requirements.txt'
$readmeLines += '  4. cd ..\frontend ; npm install'
$readmeLines += '  5. Test: uvicorn app.main:app --reload  (backend)'
$readmeLines += '          : npm run dev                   (frontend)'
$readmeLines += ''
$readmeLines += 'See MIGRATION.md for full instructions.'
$readmeLines -join "`r`n" | Out-File -FilePath $readmePath -Encoding utf8

# ---------- 3. Compress ----------
Write-Host ""
Write-Host "[3/4] Creating zip..." -ForegroundColor Yellow
if (Test-Path $ZipPath) { Remove-Item $ZipPath }
Compress-Archive -Path (Join-Path $BundleDir '*') -DestinationPath $ZipPath -CompressionLevel Optimal -Force
$zipSize = [math]::Round((Get-Item $ZipPath).Length / 1KB, 2)
$zipMsg = "  OK: " + $ZipPath + " (" + $zipSize + " KB)"
Write-Host $zipMsg -ForegroundColor Green

# ---------- 4. Cleanup ----------
Write-Host ""
Write-Host "[4/4] Cleanup..." -ForegroundColor Yellow
Remove-Item -Recurse -Force $BundleDir
Write-Host "  OK: staging directory removed" -ForegroundColor Green

# ---------- Summary ----------
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host " Done!" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host ("  File: " + $ZipPath) -ForegroundColor White
Write-Host ("  Size: " + $zipSize + " KB") -ForegroundColor White
Write-Host ""
Write-Host "  Next steps:" -ForegroundColor Yellow
Write-Host "  1. Transfer the zip to the new PC (USB or password-protected cloud)" -ForegroundColor White
Write-Host "  2. Delete the zip from cloud once migration is complete" -ForegroundColor White
Write-Host "  3. Follow the steps in MIGRATION.md on the new PC" -ForegroundColor White
Write-Host ""
