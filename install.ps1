# install.ps1 — JKAnime Downloader installer for Windows
# Run with: powershell -ExecutionPolicy Bypass -File install.ps1

$ErrorActionPreference = "Stop"

function Info    { Write-Host "  > $args" -ForegroundColor Cyan }
function Success { Write-Host "  v $args" -ForegroundColor Green }
function Warn    { Write-Host "  ! $args" -ForegroundColor Yellow }
function Fail    { Write-Host "  x $args" -ForegroundColor Red; exit 1 }

Write-Host ""
Write-Host "  JKAnime Downloader -- Windows Installer" -ForegroundColor White
Write-Host "  ----------------------------------------"
Write-Host ""

# ── 1. Python 3.10+ ───────────────────────────────────────────────────────────
Info "Checking Python version..."
try {
    $pyver = & python --version 2>&1
    $parts = ($pyver -replace "Python ", "").Split(".")
    if ([int]$parts[0] -lt 3 -or ([int]$parts[0] -eq 3 -and [int]$parts[1] -lt 10)) {
        Fail "Python 3.10+ required. Download from https://python.org"
    }
    Success "Found $pyver"
} catch {
    Fail "Python not found. Download from https://python.org"
}

# ── 2. ffmpeg ─────────────────────────────────────────────────────────────────
Info "Checking ffmpeg..."
$ffmpegOk = $null -ne (Get-Command ffmpeg -ErrorAction SilentlyContinue)
if ($ffmpegOk) {
    Success "ffmpeg found"
} else {
    Warn "ffmpeg not found -- trying winget..."
    try {
        winget install --id Gyan.FFmpeg -e --silent
        Success "ffmpeg installed via winget"
    } catch {
        Warn "Could not install ffmpeg automatically."
        Warn "Download from: https://ffmpeg.org/download.html"
        Warn "Make sure ffmpeg.exe is in your PATH before running the app."
    }
}

# ── 3. yt-dlp ─────────────────────────────────────────────────────────────────
Info "Checking yt-dlp..."
$ytdlpOk = $null -ne (Get-Command yt-dlp -ErrorAction SilentlyContinue)
if ($ytdlpOk) {
    Success "yt-dlp found"
} else {
    Warn "yt-dlp not found -- trying winget..."
    try {
        winget install --id yt-dlp.yt-dlp -e --silent
        Success "yt-dlp installed via winget"
    } catch {
        Warn "Could not install yt-dlp automatically."
        Warn "Download from: https://github.com/yt-dlp/yt-dlp/releases"
    }
}

# ── 4. Virtual environment ────────────────────────────────────────────────────
Info "Creating virtual environment (.venv)..."
python -m venv .venv
Success "Virtual environment created"

# ── 5. Dependencies ───────────────────────────────────────────────────────────
Info "Installing Python dependencies..."
& .\.venv\Scripts\pip install --upgrade pip -q
& .\.venv\Scripts\pip install -r requirements.txt -q
Success "Dependencies installed (requests, beautifulsoup4, PyQt6, yt-dlp)"

# ── 6. Launcher scripts ───────────────────────────────────────────────────────
Info "Creating launcher scripts..."

@"
@echo off
"%~dp0.venv\Scripts\python.exe" "%~dp0jkanime_gui.py" %*
"@ | Set-Content -Path "jkanime-gui.bat" -Encoding ASCII

@"
@echo off
"%~dp0.venv\Scripts\python.exe" "%~dp0jkanime_downloader.py" %*
"@ | Set-Content -Path "jkanime.bat" -Encoding ASCII

Success "Launchers created: jkanime-gui.bat  and  jkanime.bat"

# ── Done ──────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "  Installation complete!" -ForegroundColor White
Write-Host ""
Write-Host "  Run the GUI:  " -NoNewline; Write-Host "jkanime-gui.bat" -ForegroundColor Cyan
Write-Host "  Run the CLI:  " -NoNewline; Write-Host "jkanime.bat naruto --listar" -ForegroundColor Cyan
Write-Host ""
