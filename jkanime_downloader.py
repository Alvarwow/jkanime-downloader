#!/usr/bin/env python3
"""
jkanime_downloader.py - Descargador de animes completos de jkanime.net

Requisitos:
    pip install requests beautifulsoup4 yt-dlp

Uso CLI:
    python3 jkanime_downloader.py naruto
    python3 jkanime_downloader.py naruto --ep-inicio 5 --ep-fin 10
    python3 jkanime_downloader.py naruto --servidor Streamtape
    python3 jkanime_downloader.py naruto --listar

Uso GUI:
    python3 jkanime_gui.py

El "slug" es la parte de la URL de jkanime.net después del dominio.
Por ejemplo:  https://jkanime.net/naruto-shippuden/  →  naruto-shippuden
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
    print("ERROR: Faltan dependencias. Instala con: pip install requests beautifulsoup4")
    sys.exit(1)

BASE_URL = "https://jkanime.net"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": BASE_URL + "/",
}

# Servidores en orden de preferencia (Mediafire primero: descarga directa sin límites)
SERVIDORES_PREFERIDOS = [
    "Mediafire", "Mp4upload", "Streamwish", "Vidhide", "VOE",
    "Mixdrop", "Streamtape", "Doodstream",
]


class JKAnimeDownloader:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.csrf_token = None
        self._cancelar = False  # flag para abortar desde la GUI

    def cancelar(self):
        self._cancelar = True

    def _obtener_csrf(self, url: str) -> str:
        """Obtiene el token CSRF de una página."""
        resp = self.session.get(url, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        meta = soup.find("meta", {"name": "csrf-token"})
        if meta:
            return meta.get("content", "")
        return ""

    def obtener_info_anime(self, slug: str, log=print) -> dict:
        """Obtiene el ID, nombre y episodios totales del anime."""
        url = f"{BASE_URL}/{slug}/"
        log(f"Obteniendo información de: {url}")

        self.csrf_token = self._obtener_csrf(url)
        resp = self.session.get(url, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Extraer ID del anime desde los endpoints AJAX embebidos
        match = re.search(r'ajax/episodes/(\d+)', resp.text)
        if not match:
            raise ValueError(f"No se pudo encontrar el ID del anime para '{slug}'")
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
        """Obtiene la lista completa de episodios paginando el API."""
        episodios = []
        pagina = 1

        log(f"Listando episodios del anime ID {anime_id}...")

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

        log(f"Total de episodios encontrados: {len(episodios)}")
        return episodios

    def obtener_servidores(self, slug: str, numero_ep: int) -> list[dict]:
        """
        Obtiene la lista de servidores de un episodio.
        Retorna lista de dicts con: server, url_embed, size, lang
        """
        url = f"{BASE_URL}/{slug}/{numero_ep}/"
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
                "server": s.get("server", "Desconocido"),
                "url": url_embed,
                "size": s.get("size", "?"),
                "lang": s.get("lang", 1),  # 1=sub, 2=dub
                "slug": s.get("slug", ""),
            })

        return servidores

    def _elegir_servidor(self, servidores: list[dict], servidor_pref: str | None, log=print) -> dict | None:
        """Selecciona el mejor servidor disponible."""
        if not servidores:
            return None

        subs = [s for s in servidores if s["lang"] == 1]
        candidatos = subs if subs else servidores

        if servidor_pref:
            for s in candidatos:
                if s["server"].lower() == servidor_pref.lower():
                    return s
            log(f"Servidor '{servidor_pref}' no disponible para este episodio.")

        for nombre_pref in SERVIDORES_PREFERIDOS:
            for s in candidatos:
                if s["server"].lower() == nombre_pref.lower():
                    return s

        return candidatos[0]

    def descargar_mediafire(self, url_mf: str, archivo_salida: str,
                             log=print, on_progress=None) -> bool:
        """Extrae el enlace directo de Mediafire y lo descarga."""
        log(f"Extrayendo enlace de Mediafire...")
        try:
            resp = self.session.get(url_mf, timeout=20)
            resp.raise_for_status()
            match = re.search(r'href="(https://download\d+\.mediafire\.com/[^"]+\.(?:mp4|mkv|avi))"', resp.text)
            if not match:
                log("  No se encontró enlace directo en Mediafire.")
                return False
            url_directa = match.group(1)
            log(f"  Enlace directo: {url_directa[:80]}...")
            return self.descargar_directo(url_directa, archivo_salida, log, on_progress)
        except Exception as e:
            log(f"  Error con Mediafire: {e}")
            return False

    def descargar_con_ytdlp(self, url_video: str, archivo_salida: str, log=print) -> bool:
        """Usa yt-dlp para descargar el video."""
        # Buscar yt-dlp: primero en PATH, luego en ~/.local/bin
        ytdlp_path = None
        for candidato in ["yt-dlp", os.path.expanduser("~/.local/bin/yt-dlp")]:
            try:
                subprocess.run([candidato, "--version"], capture_output=True, check=True)
                ytdlp_path = candidato
                break
            except (FileNotFoundError, subprocess.CalledProcessError):
                continue

        if not ytdlp_path:
            log("yt-dlp no encontrado. Instálalo: pacman -S yt-dlp  o  curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o ~/.local/bin/yt-dlp && chmod +x ~/.local/bin/yt-dlp")
            return False

        cmd = [
            ytdlp_path,
            "--no-warnings",
            "--newline",          # una línea por actualización de progreso
            "-o", archivo_salida,
            "--retries", "5",
            "--fragment-retries", "10",
            "--concurrent-fragments", "4",
            url_video,
        ]

        log(f"Descargando con yt-dlp: {url_video[:80]}...")
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
                log(f"yt-dlp terminó con código {proc.returncode}")
            return proc.returncode == 0
        except Exception as e:
            log(f"Error ejecutando yt-dlp: {e}")
            return False

    def descargar_directo(self, url_video: str, archivo_salida: str,
                          log=print, on_progress=None) -> bool:
        """Descarga directamente con requests + callback de progreso."""
        log(f"Descarga directa: {url_video[:80]}...")
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
            log(f"Error de descarga directa: {e}")
            return False

    def descargar_episodio(
        self,
        slug: str,
        numero_ep: int,
        carpeta: str,
        servidor_pref: str | None = None,
        log=print,
        on_progress=None,
    ) -> bool:
        """Descarga un episodio concreto probando todos los servidores hasta que uno funcione."""
        archivo_destino = os.path.join(carpeta, f"{slug}_ep{numero_ep:04d}.%(ext)s")
        archivo_mp4 = os.path.join(carpeta, f"{slug}_ep{numero_ep:04d}.mp4")

        if os.path.exists(archivo_mp4):
            log(f"Episodio {numero_ep} ya descargado, saltando.")
            return True

        servidores = self.obtener_servidores(slug, numero_ep)
        if not servidores:
            log(f"No se encontraron servidores para el episodio {numero_ep}")
            return False

        # Construir lista ordenada: servidor preferido primero, luego el resto por preferencia
        subs = [s for s in servidores if s["lang"] == 1] or servidores
        candidatos = []
        if servidor_pref:
            primero = [s for s in subs if s["server"].lower() == servidor_pref.lower()]
            candidatos.extend(primero)
        for nombre_pref in SERVIDORES_PREFERIDOS:
            for s in subs:
                if s["server"].lower() == nombre_pref.lower() and s not in candidatos:
                    candidatos.append(s)
        for s in subs:
            if s not in candidatos:
                candidatos.append(s)

        for servidor in candidatos:
            if self._cancelar:
                return False
            log(f"Probando servidor: {servidor['server']} ({servidor['size']})")

            # Mediafire: extracción de enlace directo (no usa yt-dlp)
            if servidor["server"].lower() == "mediafire":
                ok = self.descargar_mediafire(servidor["url"], archivo_mp4, log, on_progress)
            else:
                ok = self.descargar_con_ytdlp(servidor["url"], archivo_destino, log)
                if not ok:
                    log("  yt-dlp falló, probando descarga directa...")
                    ok = self.descargar_directo(servidor["url"], archivo_mp4, log, on_progress)

            if ok:
                return True
            log(f"  Servidor {servidor['server']} falló, probando siguiente...")

        log(f"Todos los servidores fallaron para el episodio {numero_ep}.")
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
        """Punto de entrada principal: descarga todo un anime."""
        self._cancelar = False
        info = self.obtener_info_anime(slug, log)
        log(f"Anime: {info['nombre']} (ID: {info['id']})")

        episodios = self.listar_episodios(info["id"], log)
        if not episodios:
            log("No se encontraron episodios.")
            return info, []

        ep_fin_real = ep_fin or episodios[-1]["number"]
        episodios_filtrados = [
            e for e in episodios if ep_inicio <= e["number"] <= ep_fin_real
        ]

        if listar_solo:
            return info, episodios_filtrados

        if not episodios_filtrados:
            log(f"No hay episodios en el rango {ep_inicio}-{ep_fin_real}.")
            return info, []

        carpeta = os.path.join(carpeta_raiz, slug)
        os.makedirs(carpeta, exist_ok=True)
        log(f"Carpeta de destino: {os.path.abspath(carpeta)}")
        log(f"Descargando {len(episodios_filtrados)} episodios (del {ep_inicio} al {ep_fin_real})")

        exitos = 0
        fallos = []

        for i, ep in enumerate(episodios_filtrados):
            if self._cancelar:
                log("Descarga cancelada.")
                break

            log(f"\n── Episodio {ep['number']}/{ep_fin_real}: {ep['title']}")
            if on_episode_start:
                on_episode_start(i + 1, len(episodios_filtrados), ep["title"])

            ok = self.descargar_episodio(
                slug, ep["number"], carpeta, servidor, log, on_progress
            )
            if ok:
                exitos += 1
            else:
                fallos.append(ep["number"])

            if on_episode_done:
                on_episode_done(ep["number"], ok)

            time.sleep(1)

        log(f"\n── Descarga completada: {exitos}/{len(episodios_filtrados)} episodios")
        if fallos:
            log(f"Episodios fallidos: {fallos}")

        return info, episodios_filtrados


def main():
    parser = argparse.ArgumentParser(
        description="Descargador de animes de jkanime.net",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  %(prog)s naruto
  %(prog)s naruto-shippuden --ep-inicio 1 --ep-fin 50
  %(prog)s one-piece --servidor Streamtape --carpeta ~/Videos/Anime
  %(prog)s attack-on-titan --listar
        """,
    )
    parser.add_argument("slug", help="Nombre del anime en la URL (ej: naruto, one-piece)")
    parser.add_argument("--ep-inicio", type=int, default=1, help="Episodio inicial (default: 1)")
    parser.add_argument("--ep-fin", type=int, default=None, help="Episodio final (default: último)")
    parser.add_argument(
        "--servidor",
        default=None,
        help=f"Servidor preferido. Opciones: {', '.join(SERVIDORES_PREFERIDOS)}",
    )
    parser.add_argument("--carpeta", default=".", help="Carpeta de descarga (default: directorio actual)")
    parser.add_argument("--listar", action="store_true", help="Solo listar episodios sin descargar")

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
            print(f"\nEpisodios de {info['nombre']}:")
            for ep in eps:
                print(f"  Ep {ep['number']:4d} | {ep['title']}")
    except KeyboardInterrupt:
        print("\n[!] Descarga interrumpida por el usuario.")
    except Exception as e:
        print(f"\n[!] Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
