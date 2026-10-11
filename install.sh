#!/usr/bin/env bash
# install.sh — JKAnime Downloader installer
set -e

BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
RESET='\033[0m'

info()    { echo -e "${CYAN}  ▸ $*${RESET}"; }
success() { echo -e "${GREEN}  ✓ $*${RESET}"; }
warn()    { echo -e "${YELLOW}  ⚠ $*${RESET}"; }
error()   { echo -e "${RED}  ✖ $*${RESET}"; exit 1; }

echo ""
echo -e "${BOLD}  JKAnime Downloader — Installer${RESET}"
echo -e "  ────────────────────────────────"
echo ""

# ── 1. Python 3.10+ ──────────────────────────────────────────────────────────
info "Checking Python version..."
if ! command -v python3 &>/dev/null; then
    error "Python 3 not found. Install it from https://python.org"
fi
PY_VER=$(python3 -c "import sys; print(sys.version_info[:2] >= (3,10))")
if [ "$PY_VER" != "True" ]; then
    error "Python 3.10 or higher is required."
fi
success "Python $(python3 --version | cut -d' ' -f2) found"

# ── 2. ffmpeg ─────────────────────────────────────────────────────────────────
info "Checking ffmpeg..."
if command -v ffmpeg &>/dev/null; then
    success "ffmpeg found"
else
    warn "ffmpeg not found — trying to install..."
    if command -v pacman  &>/dev/null; then sudo pacman -S --noconfirm ffmpeg
    elif command -v apt    &>/dev/null; then sudo apt install -y ffmpeg
    elif command -v dnf    &>/dev/null; then sudo dnf install -y ffmpeg
    elif command -v brew   &>/dev/null; then brew install ffmpeg
    else
        warn "Could not install ffmpeg automatically."
        warn "Please install it manually: https://ffmpeg.org/download.html"
    fi
fi

# ── 3. Virtual environment ────────────────────────────────────────────────────
info "Creating virtual environment (.venv)..."
python3 -m venv .venv
success "Virtual environment created"

# ── 4. pip inside venv ───────────────────────────────────────────────────────
info "Installing Python dependencies..."
.venv/bin/pip install --upgrade pip -q
.venv/bin/pip install -r requirements.txt -q
success "Dependencies installed (requests, beautifulsoup4, PyQt6, yt-dlp)"

# ── 5. Launcher scripts ───────────────────────────────────────────────────────
info "Creating launcher scripts..."

cat > jkanime-gui << 'EOF'
#!/usr/bin/env bash
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"$DIR/.venv/bin/python3" "$DIR/jkanime_gui.py" "$@"
EOF

cat > jkanime << 'EOF'
#!/usr/bin/env bash
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"$DIR/.venv/bin/python3" "$DIR/jkanime_downloader.py" "$@"
EOF

chmod +x jkanime-gui jkanime
success "Launchers created: ./jkanime-gui  and  ./jkanime"

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}  Installation complete!${RESET}"
echo ""
echo -e "  Run the GUI:  ${CYAN}./jkanime-gui${RESET}"
echo -e "  Run the CLI:  ${CYAN}./jkanime naruto --listar${RESET}"
echo ""
