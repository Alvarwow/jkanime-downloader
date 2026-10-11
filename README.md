<div align="center">

# ⬛ JKAnime Downloader

**Descarga animes completos de [jkanime.net](https://jkanime.net) con interfaz gráfica o desde la terminal.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-white?style=flat-square&logo=python&logoColor=white&labelColor=0a0a0a)](https://python.org)
[![PyQt6](https://img.shields.io/badge/PyQt6-GUI-c8a96e?style=flat-square&logo=qt&logoColor=white&labelColor=0a0a0a)](https://pypi.org/project/PyQt6/)
[![yt-dlp](https://img.shields.io/badge/yt--dlp-powered-white?style=flat-square&logo=youtube&logoColor=white&labelColor=0a0a0a)](https://github.com/yt-dlp/yt-dlp)
[![License: MIT](https://img.shields.io/badge/License-MIT-555?style=flat-square&labelColor=0a0a0a)](LICENSE)

</div>

---

## ✦ Características

- **Interfaz gráfica** oscura y premium construida con PyQt6
- **Descarga animes completos** o rangos de episodios específicos
- **Multiples servidores** — prueba automáticamente todos hasta encontrar uno que funcione
- **Prioridad Mediafire** — descarga directa sin limitaciones de velocidad
- **yt-dlp integrado** para servidores de streaming (Mp4upload, VOE, Streamtape…)
- **Reanudación** — los episodios ya descargados se saltan automáticamente
- **CLI disponible** para uso sin interfaz gráfica

---

## ✦ Instalación

### Requisitos previos

- Python 3.10 o superior
- `ffmpeg` instalado en el sistema

```bash
# Arch Linux
sudo pacman -S ffmpeg yt-dlp

# Ubuntu / Debian
sudo apt install ffmpeg
pip install yt-dlp
```

### Dependencias Python

```bash
pip install -r requirements.txt
```

> Si tu sistema no tiene `pip`, descarga `yt-dlp` manualmente:
> ```bash
> curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp \
>   -o ~/.local/bin/yt-dlp && chmod +x ~/.local/bin/yt-dlp
> ```

---

## ✦ Uso

### Interfaz gráfica

```bash
python3 jkanime_gui.py
```

1. Pega la URL del anime (ej: `https://jkanime.net/cyberpunk-edgerunners/`)
2. Pulsa **Buscar episodios**
3. Configura el rango y la carpeta de destino
4. Pulsa **Descargar**

### Línea de comandos

```bash
# Descargar anime completo
python3 jkanime_downloader.py naruto

# Descargar rango de episodios
python3 jkanime_downloader.py naruto-shippuden --ep-inicio 1 --ep-fin 50

# Elegir servidor específico
python3 jkanime_downloader.py one-piece --servidor Mediafire

# Guardar en carpeta específica
python3 jkanime_downloader.py attack-on-titan --carpeta ~/Videos/Anime

# Solo listar episodios disponibles
python3 jkanime_downloader.py cyberpunk-edgerunners --listar
```

#### Opciones CLI

| Argumento | Descripción | Valor por defecto |
|---|---|---|
| `slug` | Nombre del anime en la URL | — |
| `--ep-inicio` | Episodio desde el que empezar | `1` |
| `--ep-fin` | Episodio hasta el que descargar | último |
| `--servidor` | Servidor preferido | Auto (Mediafire primero) |
| `--carpeta` | Carpeta de destino | directorio actual |
| `--listar` | Solo listar, sin descargar | — |

---

## ✦ Servidores soportados

El descargador prueba los servidores en este orden hasta que uno funcione:

| # | Servidor | Método |
|---|---|---|
| 1 | **Mediafire** | Descarga directa (extracción de enlace) |
| 2 | **Mp4upload** | yt-dlp |
| 3 | **Streamwish** | yt-dlp |
| 4 | **Vidhide** | yt-dlp |
| 5 | **VOE** | yt-dlp |
| 6 | **Mixdrop** | yt-dlp |
| 7 | **Streamtape** | yt-dlp |
| 8 | **Doodstream** | yt-dlp |

---

## ✦ Estructura del proyecto

```
jkanime-downloader/
├── jkanime_downloader.py   # Núcleo: scraping + descarga (usable como CLI o librería)
├── jkanime_gui.py          # Interfaz gráfica PyQt6
├── requirements.txt
├── LICENSE
└── README.md
```

---

## ✦ Cómo funciona

```
URL del anime
     │
     ▼
jkanime.net/{slug}/          →  extrae ID interno del anime
     │
     ▼
/ajax/episodes/{id}/{página}  →  lista paginada de episodios (JSON)
     │
     ▼
jkanime.net/{slug}/{numero}/  →  extrae lista de servidores (base64 en JS)
     │
     ├─ Mediafire  →  scraping del enlace directo  →  descarga con requests
     └─ Otros      →  yt-dlp extrae URL de stream  →  descarga con yt-dlp
```

---

## ✦ Aviso legal

Este proyecto es solo para uso educativo y personal. Respeta los derechos de autor y las condiciones de uso de [jkanime.net](https://jkanime.net). No almacenes ni distribuyas el contenido descargado.

---

<div align="center">
<sub>Hecho con Python · PyQt6 · yt-dlp</sub>
</div>
