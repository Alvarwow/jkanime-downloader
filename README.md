<div align="center">

# ⬛ JKAnime Downloader

**Download complete anime series from [jkanime.net](https://jkanime.net) — GUI or CLI.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-white?style=flat-square&logo=python&logoColor=white&labelColor=0a0a0a)](https://python.org)
[![PyQt6](https://img.shields.io/badge/PyQt6-GUI-c8a96e?style=flat-square&logo=qt&logoColor=white&labelColor=0a0a0a)](https://pypi.org/project/PyQt6/)
[![yt-dlp](https://img.shields.io/badge/yt--dlp-powered-white?style=flat-square&logo=youtube&logoColor=white&labelColor=0a0a0a)](https://github.com/yt-dlp/yt-dlp)
[![License: MIT](https://img.shields.io/badge/License-MIT-555?style=flat-square&labelColor=0a0a0a)](LICENSE)
[![Ko-fi](https://img.shields.io/badge/Ko--fi-Support-c8a96e?style=flat-square&logo=ko-fi&logoColor=white&labelColor=0a0a0a)](https://ko-fi.com/YOUR_KOFI_USERNAME)

</div>

---

## ✦ Features

- **Premium dark GUI** built with PyQt6
- **Download full series** or specific episode ranges
- **Automatic server fallback** — tries every available server until one works
- **Mediafire first** — direct download, no speed limits
- **yt-dlp integration** for streaming servers (Mp4upload, VOE, Streamtape…)
- **Resume support** — already downloaded episodes are skipped automatically
- **Jellyfin-ready filenames** — `Anime Name - S01E01.mp4`
- **CLI available** for scripting and headless use

---

## ✦ Installation

### One-line install (recommended)

```bash
git clone https://github.com/YOUR_USERNAME/jkanime-downloader.git
cd jkanime-downloader
bash install.sh
```

The installer will:
- Check Python 3.10+ is available
- Install `ffmpeg` if missing (supports apt, pacman, dnf, brew)
- Create an isolated virtual environment (`.venv/`)
- Install all Python dependencies inside it
- Generate ready-to-run launcher scripts

After installation, just run:

```bash
./jkanime-gui        # graphical interface
./jkanime --help     # command-line interface
```

### Manual install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

> **ffmpeg** must also be installed on your system:
> ```bash
> # Arch Linux
> sudo pacman -S ffmpeg
> # Ubuntu / Debian
> sudo apt install ffmpeg
> # macOS
> brew install ffmpeg
> ```

---

## ✦ Usage

### GUI

```bash
./jkanime-gui
# or: python3 jkanime_gui.py
```

1. Paste the anime URL (e.g. `https://jkanime.net/cyberpunk-edgerunners/`)
2. Click **Search episodes**
3. Set the episode range and destination folder
4. Click **Download**

### CLI

```bash
# Download a full series
./jkanime naruto

# Download a specific range
./jkanime naruto-shippuden --ep-start 1 --ep-end 50

# Choose a specific server
./jkanime one-piece --server Mediafire

# Save to a custom folder
./jkanime attack-on-titan --folder ~/Videos/Anime

# List available episodes without downloading
./jkanime cyberpunk-edgerunners --list
```

#### CLI options

| Argument | Description | Default |
|---|---|---|
| `slug` | Anime name from the URL | — |
| `--ep-inicio` | First episode to download | `1` |
| `--ep-fin` | Last episode to download | last |
| `--servidor` | Preferred server | Auto (Mediafire first) |
| `--carpeta` | Destination folder | current directory |
| `--listar` | List episodes only, no download | — |

---

## ✦ Supported servers

Servers are tried in this order until one succeeds:

| Priority | Server | Method |
|:---:|---|---|
| 1 | **Mediafire** | Direct link extraction |
| 2 | **Mp4upload** | yt-dlp |
| 3 | **Streamwish** | yt-dlp |
| 4 | **Vidhide** | yt-dlp |
| 5 | **VOE** | yt-dlp |
| 6 | **Mixdrop** | yt-dlp |
| 7 | **Streamtape** | yt-dlp |
| 8 | **Doodstream** | yt-dlp |

---

## ✦ Output format

Files are named for **Jellyfin / Plex / Emby** compatibility:

```
~/Videos/Anime/
└── Cyberpunk Edgerunners/
    ├── Cyberpunk Edgerunners - S01E01.mp4
    ├── Cyberpunk Edgerunners - S01E02.mp4
    └── ...
```

---

## ✦ Project structure

```
jkanime-downloader/
├── jkanime_downloader.py   # Core engine — scraping, downloading, CLI
├── jkanime_gui.py          # PyQt6 graphical interface
├── install.sh              # Automated installer
├── requirements.txt        # Python dependencies
├── LICENSE
└── README.md
```

---

## ✦ How it works

```
Anime URL
    │
    ▼
jkanime.net/{slug}/           →  extract internal anime ID
    │
    ▼
/ajax/episodes/{id}/{page}    →  paginated episode list (JSON)
    │
    ▼
jkanime.net/{slug}/{number}/  →  extract server list (base64-encoded in JS)
    │
    ├─ Mediafire  →  scrape direct download link  →  stream with requests
    └─ Others     →  yt-dlp resolves stream URL   →  download with yt-dlp
```

---

## ✦ Support the project

JKAnime Downloader is free and open source. If it saves you time or you just find it useful, consider buying me a coffee — it helps keep the project maintained and motivates adding new features.

<div align="center">

[![Ko-fi](https://img.shields.io/badge/Ko--fi-Support-c8a96e?style=for-the-badge&logo=ko-fi&logoColor=white&labelColor=0a0a0a)](https://ko-fi.com/YOUR_KOFI_USERNAME)

</div>

> No pressure at all — a GitHub ⭐ star on the repo is already a great way to show support.

---

## ✦ Legal notice

This project is for personal and educational use only. Respect the copyright and terms of service of [jkanime.net](https://jkanime.net). Do not redistribute downloaded content.

---

<div align="center">
<sub>Built with Python · PyQt6 · yt-dlp</sub>
</div>

