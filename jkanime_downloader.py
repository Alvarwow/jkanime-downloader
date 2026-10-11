#!/usr/bin/env python3
"""
jkanime_downloader.py - Full anime series downloader for jkanime.net

Requirements:
    pip install requests beautifulsoup4 yt-dlp

CLI usage:
    python3 jkanime_downloader.py naruto
    python3 jkanime_downloader.py naruto --ep-inicio 5 --ep-fin 10
    python3 jkanime_downloader.py naruto --servidor Streamtape
    python3 jkanime_downloader.py naruto --listar

GUI usage:
    python3 jkanime_gui.py

The "slug" is the part of the jkanime.net URL after the domain.
Example:  https://jkanime.net/naruto-shippuden/  →  naruto-shippuden
"""

import argparse
import base64
import json
import os
import re
import subprocess
import sys
import time
from urllib.parse import urljoin

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("ERROR: Missing dependencies. Install with: pip install requests beautifulsoup4")
    sys.exit(1)

BASE_URL = "https://jkanime.net"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": BASE_URL + "/",
}

# Servers in order of preference (Mediafire first: direct download, no speed limits)
PREFERRED_SERVERS = [
    "Mediafire", "Mp4upload", "Streamwish", "Vidhide", "VOE",
    "Mixdrop", "Streamtape", "Doodstream",
]


def _sanitize_name(name: str) -> str:
    """Strip filesystem-illegal characters from an anime name."""
    return re.sub(r'[\\/:*?"<>|]', '', name).strip()


def _jellyfin_filename(anime_name: str, episode: int, ext: str = "%(ext)s") -> str:
    """Build a Jellyfin-compatible filename: 'Anime Name - S01E01.ext'"""
    clean = _sanitize_name(anime_name)
    return f"{clean} - S01E{episode:02d}.{ext}"


class JKAnimeDownloader:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.csrf_token = None
        self._cancelar = False  # flag para abortar desde la GUI

    def cancelar(self):
        self._cancelar = True

    def _obtener_csrf(self, url: str) -> str:
        """Fetch the CSRF token from a page."""
        resp = self.session.get(url, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        meta = soup.find("meta", {"name": "csrf-token"})
        if meta:
            return meta.get("content", "")
        return ""

    def obtener_info_anime(self, slug: str, log=print) -> dict:
        """Fetch the anime ID, title and total episode count."""
        url = f"{BASE_URL}/{slug}/"
        log(f"Fetching anime info: {url}")

        self.csrf_token = self._obtener_csrf(url)
        resp = self.session.get(url, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Extraer ID del anime desde los endpoints AJAX embebidos
        match = re.search(r'ajax/episodes/(\d+)', resp.text)
        if not match:
            raise ValueError(f"Could not find anime ID for '{slug}'")
        anime_id = match.group(1)

        # Extraer nombre del anime (el h3 dentro de .anime_info)
        anime_info = soup.find(class_="anime_info")
        if anime_info:
            titulo = anime_info.find("h3")
        else:
            titulo = None
        nombre = titulo.text.strip() if titulo else slug

        # Extraer total de episodios
        total_ep = 0
        li_eps = soup.find("li", string=re.compile(r"Episodios:"))
        if li_eps:
            total_ep = int(re.search(r'\d+', li_eps.text).group())
        else:
            total_ep = None

        return {"id": anime_id, "nombre": nombre, "slug": slug, "total": total_ep}

    def listar_episodios(self, anime_id: str, log=print) -> list[dict]:
        """Fetch the full episode list by paginating the API."""
        episodios = []
        pagina = 1

        log(f"Listing episodes for anime ID {anime_id}...")

        while True:
            url_pag = f"{BASE_URL}/ajax/episodes/{anime_id}/{pagina}"
            resp = self.session.post(
                url_pag,
                headers={
                    "X-Requested-With": "XMLHttpRequest",
                    "X-CSRF-TOKEN": self.csrf_token or "",
                    "Referer": BASE_URL + "/",
                },
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()

            vistos = {e["id"] for e in episodios}
            for ep in data.get("data", []):
                if ep["id"] not in vistos:
                    episodios.append(ep)
                    vistos.add(ep["id"])

            ultima_pag = data.get("last_page", 1)
            if pagina >= ultima_pag:
                break
            pagina += 1
            time.sleep(0.5)

        log(f"Total episodes found: {len(episodios)}")
        return episodios

    def obtener_servidores(self, slug: str, episode_num: int) -> list[dict]:
        """
        Obtiene la lista de servidores de un episodio.
        Retorna lista de dicts con: server, url_embed, size, lang
        """
        url = f"{BASE_URL}/{slug}/{episode_num}/"
        resp = self.session.get(url, timeout=30)
        resp.raise_for_status()

        # Buscar la variable JS `servers = [...]`
        match = re.search(r'servers\s*=\s*(\[.*?\]);', resp.text, re.DOTALL)
        if not match:
            return []

        try:
            servidores_raw = json.loads(match.group(1))
        except json.JSONDecodeError:
            return []

        servidores = []
        for s in servidores_raw:
            try:
                url_embed = base64.b64decode(s["remote"] + "==").decode("utf-8").strip()
            except Exception:
                url_embed = s.get("remote", "")

            servidores.append({
                "server": s.get("server", "Unknown"),
                "url": url_embed,
                "size": s.get("size", "?"),
                "lang": s.get("lang", 1),  # 1=sub, 2=dub
                "slug": s.get("slug", ""),
            })

        return servidores

    def _elegir_servidor(self, servidores: list[dict], servidor_pref: str | None, log=print) -> dict | None:
        """Pick the best available server."""
        if not servidores:
            return None

        subs = [s for s in servidores if s["lang"] == 1]
        candidatos = subs if subs else servidores

        if servidor_pref:
            for s in candidatos:
                if s["server"].lower() == servidor_pref.lower():
                    return s
            log(f"Server '{servidor_pref}' not available for this episode.")

        for nombre_pref in PREFERRED_SERVERS:
            for s in candidatos:
                if s["server"].lower() == nombre_pref.lower():
                    return s

        return candidatos[0]

    def descargar_mediafire(self, url_mf: str, archivo_salida: str,
                             log=print, on_progress=None) -> bool:
        """Extract the direct download link from Mediafire and download it."""
        log(f"Extracting Mediafire direct link...")
        try:
            resp = self.session.get(url_mf, timeout=20)
            resp.raise_for_status()
            match = re.search(r'href="(https://download\d+\.mediafire\.com/[^"]+\.(?:mp4|mkv|avi))"', resp.text)
            if not match:
                log("  Could not find a direct download link on Mediafire.")
                return False
            url_directa = match.group(1)
            log(f"  Direct link: {url_directa[:80]}...")
            return self.descargar_directo(url_directa, archivo_salida, log, on_progress)
        except Exception as e:
            log(f"  Mediafire error: {e}")
            return False

    def descargar_con_ytdlp(self, url_video: str, archivo_salida: str, log=print) -> bool:
        """Download a video using yt-dlp."""
        import sys as _sys
        # Search yt-dlp in PATH and common install locations across platforms
        is_win = _sys.platform == "win32"
        candidates = ["yt-dlp"]
        if is_win:
            candidates += [
                os.path.expanduser(r"~\AppData\Local\Programs\Python\Python3*\Scripts\yt-dlp.exe"),
                os.path.expanduser(r"~\AppData\Roaming\Python\Scripts\yt-dlp.exe"),
                os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "WinGet", "Links", "yt-dlp.exe"),
            ]
        else:
            candidates += [
                os.path.expanduser("~/.local/bin/yt-dlp"),
                "/usr/local/bin/yt-dlp",
            ]

        ytdlp_path = None
        for candidate in candidates:
            try:
                subprocess.run([candidate, "--version"], capture_output=True, check=True)
                ytdlp_path = candidate
                break
            except (FileNotFoundError, subprocess.CalledProcessError, OSError):
                continue

        if not ytdlp_path:
            if is_win:
                log("yt-dlp not found. Install via winget:  winget install yt-dlp  "
                    "or download from https://github.com/yt-dlp/yt-dlp/releases")
            else:
                log("yt-dlp not found. Install: pacman -S yt-dlp  or  "
                    "curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp "
                    "-o ~/.local/bin/yt-dlp && chmod +x ~/.local/bin/yt-dlp")
            return False

        cmd = [
            ytdlp_path,
            "--no-warnings",
            "--newline",          # one line per progress update
            "-o", archivo_salida,
            "--retries", "5",
            "--fragment-retries", "10",
            "--concurrent-fragments", "4",
            url_video,
        ]

        log(f"Downloading with yt-dlp: {url_video[:80]}...")
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            for line in proc.stdout:
                line = line.strip()
                if line:
                    log(line)
                if self._cancelar:
                    proc.terminate()
                    return False
            proc.wait()
            if proc.returncode != 0:
                log(f"yt-dlp exited with code {proc.returncode}")
            return proc.returncode == 0
        except Exception as e:
            log(f"Error running yt-dlp: {e}")
            return False

    def descargar_directo(self, url_video: str, archivo_salida: str,
                          log=print, on_progress=None) -> bool:
        """Download directly with requests, reporting progress via callback."""
        log(f"Direct download: {url_video[:80]}...")
        try:
            with self.session.get(url_video, stream=True, timeout=60) as r:
                r.raise_for_status()
                total = int(r.headers.get("content-length", 0))
                descargado = 0
                with open(archivo_salida, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1024 * 256):
                        if self._cancelar:
                            return False
                        if chunk:
                            f.write(chunk)
                            descargado += len(chunk)
                            if on_progress and total:
                                on_progress(descargado, total)
            return True
        except Exception as e:
            log(f"Direct download error: {e}")
            return False

    def descargar_episodio(
        self,
        slug: str,
        episode_num: int,
        carpeta: str,
        anime_name: str = "",      # nombre real para el formato Jellyfin
        servidor_pref: str | None = None,
        log=print,
        on_progress=None,
    ) -> bool:
        """Download a single episode, trying every server until one succeeds."""
        archivo_destino = os.path.join(carpeta, _jellyfin_filename(anime_name or slug, episode_num, "%(ext)s"))
        archivo_mp4    = os.path.join(carpeta, _jellyfin_filename(anime_name or slug, episode_num, "mp4"))

        if os.path.exists(archivo_mp4):
            log(f"Episode {episode_num} already downloaded, skipping.")
            return True

        servidores = self.obtener_servidores(slug, episode_num)
        if not servidores:
            log(f"No servers found for episode {episode_num}")
            return False

        # Construir lista ordenada: servidor preferido primero, luego el resto por preferencia
        subs = [s for s in servidores if s["lang"] == 1] or servidores
        candidatos = []
        if servidor_pref:
            primero = [s for s in subs if s["server"].lower() == servidor_pref.lower()]
            candidatos.extend(primero)
        for nombre_pref in PREFERRED_SERVERS:
            for s in subs:
                if s["server"].lower() == nombre_pref.lower() and s not in candidatos:
                    candidatos.append(s)
        for s in subs:
            if s not in candidatos:
                candidatos.append(s)

        for servidor in candidatos:
            if self._cancelar:
                return False
            log(f"Trying server: {servidor['server']} ({servidor['size']})")

            # Mediafire: extract direct link (no yt-dlp needed)
            if servidor["server"].lower() == "mediafire":
                ok = self.descargar_mediafire(servidor["url"], archivo_mp4, log, on_progress)
            else:
                ok = self.descargar_con_ytdlp(servidor["url"], archivo_destino, log)
                if not ok:
                    log("  yt-dlp failed, trying direct download...")
                    ok = self.descargar_directo(servidor["url"], archivo_mp4, log, on_progress)

            if ok:
                return True
            log(f"  Server {servidor['server']} failed, trying next...")

        log(f"All servers failed for episode {episode_num}.")
        return False

    def descargar_anime(
        self,
        slug: str,
        ep_inicio: int = 1,
        ep_fin: int | None = None,
        servidor: str | None = None,
        carpeta_raiz: str = ".",
        listar_solo: bool = False,
        log=print,
        on_episode_start=None,   # callback(numero, total, titulo)
        on_episode_done=None,    # callback(numero, exito)
        on_progress=None,        # callback(bytes_descargados, bytes_total)
    ):
        """Main entry point: download a full anime series."""
        self._cancelar = False
        info = self.obtener_info_anime(slug, log)
        log(f"Anime: {info['nombre']} (ID: {info['id']})")

        episodios = self.listar_episodios(info["id"], log)
        if not episodios:
            log("No episodes found.")
            return info, []

        ep_fin_real = ep_fin or episodios[-1]["number"]
        episodios_filtrados = [
            e for e in episodios if ep_inicio <= e["number"] <= ep_fin_real
        ]

        if listar_solo:
            return info, episodios_filtrados

        if not episodios_filtrados:
            log(f"No episodes in range {ep_inicio}–{ep_fin_real}.")
            return info, []

        carpeta = os.path.join(carpeta_raiz, _sanitize_name(info["nombre"]))
        os.makedirs(carpeta, exist_ok=True)
        log(f"Output folder: {os.path.abspath(carpeta)}")
        log(f"Downloading {len(episodios_filtrados)} episodes ({ep_inicio} to {ep_fin_real})")

        exitos = 0
        fallos = []

        for i, ep in enumerate(episodios_filtrados):
            if self._cancelar:
                log("Download cancelled.")
                break

            log(f"\n── Episode {ep['number']}/{ep_fin_real}: {ep['title']}")
            if on_episode_start:
                on_episode_start(i + 1, len(episodios_filtrados), ep["title"])

            ok = self.descargar_episodio(
                slug, ep["number"], carpeta, info["nombre"], servidor, log, on_progress
            )
            if ok:
                exitos += 1
            else:
                fallos.append(ep["number"])

            if on_episode_done:
                on_episode_done(ep["number"], ok)

            time.sleep(1)

        log(f"\n── Download complete: {exitos}/{len(episodios_filtrados)} episodes")
        if fallos:
            log(f"Failed episodes: {fallos}")

        return info, episodios_filtrados


def main():
    parser = argparse.ArgumentParser(
        description="Download anime series from jkanime.net",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  %(prog)s naruto
  %(prog)s naruto-shippuden --ep-inicio 1 --ep-fin 50
  %(prog)s one-piece --servidor Streamtape --carpeta ~/Videos
  %(prog)s attack-on-titan --listar
        """,
    )
    parser.add_argument("slug", help="Anime slug from the URL (e.g. naruto, one-piece)")
    parser.add_argument("--ep-inicio", type=int, default=1, help="First episode (default: 1)")
    parser.add_argument("--ep-fin", type=int, default=None, help="Last episode (default: last)")
    parser.add_argument(
        "--servidor",
        default=None,
        help=f"Preferred server. Options: {', '.join(PREFERRED_SERVERS)}",
    )
    parser.add_argument("--carpeta", default=".", help="Download folder (default: current dir)")
    parser.add_argument("--listar", action="store_true", help="List episodes only, no download")

    args = parser.parse_args()

    def log(msg):
        print(msg)

    downloader = JKAnimeDownloader()
    try:
        info, eps = downloader.descargar_anime(
            slug=args.slug,
            ep_inicio=args.ep_inicio,
            ep_fin=args.ep_fin,
            servidor=args.servidor,
            carpeta_raiz=args.carpeta,
            listar_solo=args.listar,
            log=log,
        )
        if args.listar:
            print(f"\nEpisodes of {info['nombre']}:")
            for ep in eps:
                print(f"  Ep {ep['number']:4d} | {ep['title']}")
    except KeyboardInterrupt:
        print("\n[!] Download interrupted by user.")
    except Exception as e:
        print(f"\n[!] Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
