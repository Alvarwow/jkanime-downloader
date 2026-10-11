#!/usr/bin/env python3
"""
jkanime_gui.py - Graphical interface for jkanime_downloader
Requisitos: pip install PyQt6 requests beautifulsoup4 yt-dlp
Uso:       python3 jkanime_gui.py
"""

import os
import sys
import threading

from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QIcon, QColor, QPalette, QPixmap
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QSpinBox, QCheckBox,
    QTextEdit, QProgressBar, QFileDialog, QFrame, QSplitter,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox,
    QStatusBar, QSizePolicy, QAbstractItemView,
)

try:
    from jkanime_downloader import JKAnimeDownloader, PREFERRED_SERVERS
except ImportError:
    print("ERROR: jkanime_downloader.py not found in the same directory.")
    sys.exit(1)


# ── Paleta premium negra ──────────────────────────────────────────────────────
COLOR_BG        = "#0a0a0a"   # negro puro fondo
COLOR_PANEL     = "#111111"   # negro panel
COLOR_CARD      = "#191919"   # negro tarjeta
COLOR_ELEVATED  = "#222222"   # negro elevado (hover/header)
COLOR_BORDER    = "#2e2e2e"   # borde sutil
COLOR_ACCENT    = "#ffffff"   # blanco para acento primario
COLOR_ACCENT2   = "#c8a96e"   # dorado premium
COLOR_DIM       = "#888888"   # texto secundario gris
COLOR_TEXT      = "#f0f0f0"   # texto principal casi blanco
COLOR_SUBTEXT   = "#555555"   # texto muy apagado
COLOR_SUCCESS   = "#4ade80"   # verde esmeralda
COLOR_ERROR     = "#f87171"   # rojo suave
COLOR_PROGRESS  = "#c8a96e"   # dorado para barras


STYLESHEET = f"""
/* ── Base ── */
QMainWindow, QWidget {{
    background-color: {COLOR_BG};
    color: {COLOR_TEXT};
    font-family: 'Segoe UI', 'Inter', 'Ubuntu', sans-serif;
    font-size: 13px;
}}

/* ── GroupBox ── */
QGroupBox {{
    background-color: {COLOR_PANEL};
    border: 1px solid {COLOR_BORDER};
    border-radius: 10px;
    margin-top: 14px;
    padding: 14px 12px 10px 12px;
    color: {COLOR_SUBTEXT};
    font-size: 10px;
    font-weight: bold;
    letter-spacing: 2px;
    text-transform: uppercase;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 14px;
    padding: 0 6px;
    background-color: {COLOR_PANEL};
}}

/* ── Inputs ── */
QLineEdit, QSpinBox, QComboBox {{
    background-color: {COLOR_CARD};
    border: 1px solid {COLOR_BORDER};
    border-radius: 7px;
    padding: 8px 12px;
    color: {COLOR_TEXT};
    selection-background-color: {COLOR_ACCENT2};
    selection-color: #000;
}}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
    border-color: {COLOR_ACCENT2};
    background-color: {COLOR_ELEVATED};
}}
QLineEdit::placeholder {{
    color: {COLOR_SUBTEXT};
}}
QSpinBox::up-button, QSpinBox::down-button {{
    background: {COLOR_ELEVATED};
    border: none;
    width: 18px;
    border-radius: 3px;
}}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
    background: {COLOR_BORDER};
}}
QComboBox::drop-down {{
    border: none;
    width: 28px;
}}
QComboBox::down-arrow {{
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid {COLOR_DIM};
    width: 0;
    height: 0;
    margin-right: 8px;
}}
QComboBox QAbstractItemView {{
    background-color: {COLOR_CARD};
    border: 1px solid {COLOR_BORDER};
    border-radius: 7px;
    selection-background-color: {COLOR_ELEVATED};
    selection-color: {COLOR_ACCENT2};
    color: {COLOR_TEXT};
    padding: 4px;
    outline: none;
}}

/* ── Botones base ── */
QPushButton {{
    background-color: {COLOR_CARD};
    border: 1px solid {COLOR_BORDER};
    border-radius: 7px;
    padding: 8px 18px;
    color: {COLOR_TEXT};
    font-weight: 600;
    letter-spacing: 0.3px;
}}
QPushButton:hover {{
    background-color: {COLOR_ELEVATED};
    border-color: {COLOR_DIM};
    color: #fff;
}}
QPushButton:pressed {{
    background-color: {COLOR_BORDER};
}}
QPushButton:disabled {{
    background-color: {COLOR_PANEL};
    color: {COLOR_SUBTEXT};
    border-color: {COLOR_PANEL};
}}

/* ── Primary button (gold) ── */
QPushButton#btn_primary {{
    background-color: {COLOR_ACCENT2};
    border: none;
    color: #0a0a0a;
    font-size: 13px;
    font-weight: 700;
    padding: 11px 28px;
    letter-spacing: 0.5px;
    border-radius: 8px;
}}
QPushButton#btn_primary:hover {{
    background-color: #dbbe80;
}}
QPushButton#btn_primary:pressed {{
    background-color: #a8893e;
}}
QPushButton#btn_primary:disabled {{
    background-color: #3a3020;
    color: #6a5a30;
    border: none;
}}

/* ── Cancel button ── */
QPushButton#btn_cancel {{
    background-color: transparent;
    border: 1px solid #3a3a3a;
    color: {COLOR_DIM};
    font-weight: 600;
}}
QPushButton#btn_cancel:hover {{
    background-color: #2a1515;
    border-color: {COLOR_ERROR};
    color: {COLOR_ERROR};
}}
QPushButton#btn_cancel:disabled {{
    border-color: #222;
    color: #333;
}}

/* ── Folder button ── */
QPushButton#btn_folder {{
    background-color: {COLOR_CARD};
    padding: 8px 12px;
    min-width: 36px;
    max-width: 36px;
    border-color: {COLOR_BORDER};
    color: {COLOR_DIM};
    font-size: 14px;
}}
QPushButton#btn_folder:hover {{
    color: {COLOR_ACCENT2};
    border-color: {COLOR_ACCENT2};
}}

/* ── Log / TextEdit ── */
QTextEdit {{
    background-color: {COLOR_PANEL};
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    color: #999;
    font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', 'Consolas', 'Ubuntu Mono', monospace;
    font-size: 11px;
    padding: 6px;
    line-height: 1.5;
}}

/* ── Barras de progreso ── */
QProgressBar {{
    background-color: {COLOR_CARD};
    border: 1px solid {COLOR_BORDER};
    border-radius: 5px;
    text-align: center;
    color: {COLOR_TEXT};
    height: 16px;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.3px;
}}
QProgressBar::chunk {{
    background-color: {COLOR_PROGRESS};
    border-radius: 4px;
}}

/* ── Tabla ── */
QTableWidget {{
    background-color: {COLOR_PANEL};
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    gridline-color: {COLOR_CARD};
    color: {COLOR_TEXT};
    selection-background-color: {COLOR_ELEVATED};
    selection-color: {COLOR_ACCENT2};
    outline: none;
}}
QTableWidget::item {{
    padding: 5px 10px;
    border: none;
}}
QTableWidget::item:selected {{
    color: {COLOR_ACCENT2};
}}
QHeaderView::section {{
    background-color: {COLOR_CARD};
    color: {COLOR_SUBTEXT};
    border: none;
    border-bottom: 1px solid {COLOR_BORDER};
    padding: 7px 10px;
    font-weight: bold;
    font-size: 10px;
    letter-spacing: 1.5px;
    text-transform: uppercase;
}}

/* ── Labels especiales ── */
QLabel#title {{
    font-size: 20px;
    font-weight: 700;
    color: {COLOR_TEXT};
    letter-spacing: 0.5px;
}}
QLabel#subtitle {{
    font-size: 11px;
    color: {COLOR_SUBTEXT};
    letter-spacing: 0.3px;
}}

/* ── Statusbar ── */
QStatusBar {{
    background-color: {COLOR_PANEL};
    color: {COLOR_SUBTEXT};
    border-top: 1px solid {COLOR_BORDER};
    font-size: 11px;
    padding: 2px 8px;
}}

/* ── Splitter ── */
QSplitter::handle {{
    background-color: {COLOR_BORDER};
}}

/* ── Scrollbar ── */
QScrollBar:vertical {{
    background: transparent;
    width: 6px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {COLOR_ELEVATED};
    border-radius: 3px;
    min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{
    background: {COLOR_BORDER};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{
    background: transparent;
    height: 6px;
}}
QScrollBar::handle:horizontal {{
    background: {COLOR_ELEVATED};
    border-radius: 3px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
"""


# ── Worker thread ─────────────────────────────────────────────────────────────
class BuscarWorker(QThread):
    log_signal      = pyqtSignal(str)
    episodios_signal = pyqtSignal(dict, list)  # info, episodios
    error_signal    = pyqtSignal(str)

    def __init__(self, downloader, slug):
        super().__init__()
        self.downloader = downloader
        self.slug = slug

    def run(self):
        try:
            info = self.downloader.obtener_info_anime(self.slug, self.log_signal.emit)
            eps  = self.downloader.listar_episodios(info["id"], self.log_signal.emit)
            self.episodios_signal.emit(info, eps)
        except Exception as e:
            self.error_signal.emit(str(e))


class DescargaWorker(QThread):
    log_signal      = pyqtSignal(str)
    progreso_signal = pyqtSignal(int, int)     # descargado, total
    episodio_signal = pyqtSignal(int, int, str)  # actual, total, titulo
    done_signal     = pyqtSignal(int, bool)    # numero_ep, exito
    finished_signal = pyqtSignal()
    error_signal    = pyqtSignal(str)

    def __init__(self, downloader, slug, ep_inicio, ep_fin, servidor, carpeta):
        super().__init__()
        self.downloader = downloader
        self.slug       = slug
        self.ep_inicio  = ep_inicio
        self.ep_fin     = ep_fin
        self.servidor   = servidor if not servidor.startswith("Auto") else None
        self.carpeta    = carpeta

    def run(self):
        try:
            self.downloader.descargar_anime(
                slug=self.slug,
                ep_inicio=self.ep_inicio,
                ep_fin=self.ep_fin,
                servidor=self.servidor,
                carpeta_raiz=self.carpeta,
                log=self.log_signal.emit,
                on_episode_start=self.episodio_signal.emit,
                on_episode_done=self.done_signal.emit,
                on_progress=self.progreso_signal.emit,
            )
        except Exception as e:
            self.error_signal.emit(str(e))
        finally:
            self.finished_signal.emit()


# ── Ventana principal ─────────────────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.downloader = JKAnimeDownloader()
        self.episodios  = []
        self.info_anime = {}
        self._worker    = None

        self.setWindowTitle("JKAnime Downloader")
        self.setMinimumSize(980, 700)
        self.resize(1100, 750)
        self.setStyleSheet(STYLESHEET)
        self._build_ui()
        self._status("Ready.")

    # ── UI construction ─────────────────────────────────────────────────
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(20, 16, 20, 12)
        root.setSpacing(14)

        root.addLayout(self._build_header())
        root.addWidget(self._build_search_bar())

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)

        left = self._build_left_panel()
        right = self._build_right_panel()
        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)

        root.addWidget(splitter, 1)
        root.addWidget(self._build_bottom_bar())

        self.setStatusBar(QStatusBar())

    def _build_header(self):
        lay = QHBoxLayout()

        # Left gold accent line
        accent_line = QFrame()
        accent_line.setFixedWidth(3)
        accent_line.setFixedHeight(36)
        accent_line.setStyleSheet(f"background-color: {COLOR_ACCENT2}; border-radius: 2px;")

        lbl_title = QLabel("JKAnime Downloader")
        lbl_title.setObjectName("title")
        lbl_sub = QLabel("Download complete anime series from jkanime.net")
        lbl_sub.setObjectName("subtitle")

        vlbl = QVBoxLayout()
        vlbl.setSpacing(1)
        vlbl.addWidget(lbl_title)
        vlbl.addWidget(lbl_sub)

        header_lay = QHBoxLayout()
        header_lay.setSpacing(10)
        header_lay.addWidget(accent_line)
        header_lay.addLayout(vlbl)

        lay.addLayout(header_lay)
        lay.addStretch()
        return lay

    def _build_search_bar(self):
        grp = QGroupBox("Anime URL")
        lay = QHBoxLayout(grp)
        lay.setSpacing(8)

        self.inp_slug = QLineEdit()
        self.inp_slug.setPlaceholderText(
            "Paste the anime URL  —  e.g. https://jkanime.net/cyberpunk-edgerunners/"
        )
        self.inp_slug.returnPressed.connect(self._buscar)

        self.btn_buscar = QPushButton("🔍  Search episodes")
        self.btn_buscar.setFixedWidth(180)
        self.btn_buscar.clicked.connect(self._buscar)

        lay.addWidget(self.inp_slug, 1)
        lay.addWidget(self.btn_buscar)
        return grp

    def _build_left_panel(self):
        widget = QWidget()
        lay = QVBoxLayout(widget)
        lay.setContentsMargins(0, 0, 6, 0)
        lay.setSpacing(12)

        # ── Opciones de descarga ──
        grp_opts = QGroupBox("Opciones de descarga")
        form = QVBoxLayout(grp_opts)
        form.setSpacing(10)

        # Rango de episodios
        rng_lay = QHBoxLayout()
        rng_lay.addWidget(QLabel("From ep:"))
        self.spin_inicio = QSpinBox()
        self.spin_inicio.setRange(1, 9999)
        self.spin_inicio.setValue(1)
        self.spin_inicio.setFixedWidth(70)
        rng_lay.addWidget(self.spin_inicio)
        rng_lay.addSpacing(10)
        rng_lay.addWidget(QLabel("To ep:"))
        self.spin_fin = QSpinBox()
        self.spin_fin.setRange(0, 9999)
        self.spin_fin.setValue(0)
        self.spin_fin.setSpecialValueText("Last")
        self.spin_fin.setFixedWidth(70)
        rng_lay.addWidget(self.spin_fin)
        rng_lay.addStretch()
        form.addLayout(rng_lay)

        # Servidor
        srv_lay = QHBoxLayout()
        srv_lay.addWidget(QLabel("Server:"))
        self.combo_servidor = QComboBox()
        self.combo_servidor.addItem("Auto (Mediafire first)")
        for s in PREFERRED_SERVERS:
            self.combo_servidor.addItem(s)
        srv_lay.addWidget(self.combo_servidor, 1)
        form.addLayout(srv_lay)

        # Carpeta
        folder_lay = QHBoxLayout()
        folder_lay.addWidget(QLabel("Folder:"))
        self.inp_carpeta = QLineEdit(os.path.expanduser("~/Downloads"))
        folder_lay.addWidget(self.inp_carpeta, 1)
        btn_folder = QPushButton("📁")
        btn_folder.setObjectName("btn_folder")
        btn_folder.setToolTip("Choose folder…")
        btn_folder.clicked.connect(self._elegir_carpeta)
        folder_lay.addWidget(btn_folder)
        form.addLayout(folder_lay)

        lay.addWidget(grp_opts)

        # ── Action buttons ──
        grp_acc = QGroupBox("Actions")
        acc_lay = QVBoxLayout(grp_acc)
        acc_lay.setSpacing(8)

        self.btn_descargar = QPushButton("⬇  Download")
        self.btn_descargar.setObjectName("btn_primary")
        self.btn_descargar.setEnabled(False)
        self.btn_descargar.clicked.connect(self._iniciar_descarga)

        self.btn_cancelar = QPushButton("✖  Cancel")
        self.btn_cancelar.setObjectName("btn_cancel")
        self.btn_cancelar.setEnabled(False)
        self.btn_cancelar.clicked.connect(self._cancelar_descarga)

        acc_lay.addWidget(self.btn_descargar)
        acc_lay.addWidget(self.btn_cancelar)
        lay.addWidget(grp_acc)

        # ── Progreso ──
        grp_prog = QGroupBox("Progress")
        prog_lay = QVBoxLayout(grp_prog)
        prog_lay.setSpacing(6)

        self.lbl_ep_actual = QLabel("–")
        self.lbl_ep_actual.setWordWrap(True)
        self.lbl_ep_actual.setStyleSheet(
            f"color: {COLOR_ACCENT2}; font-weight: 600; font-size: 12px;"
        )

        self.bar_episodios = QProgressBar()
        self.bar_episodios.setFormat("%v / %m episodes")
        self.bar_episodios.setValue(0)

        self.bar_bytes = QProgressBar()
        self.bar_bytes.setFormat("Direct download: %p%")
        self.bar_bytes.setValue(0)
        self.bar_bytes.setVisible(False)

        prog_lay.addWidget(self.lbl_ep_actual)
        prog_lay.addWidget(self.bar_episodios)
        prog_lay.addWidget(self.bar_bytes)
        lay.addWidget(grp_prog)

        lay.addStretch()
        return widget

    def _build_right_panel(self):
        widget = QWidget()
        lay = QVBoxLayout(widget)
        lay.setContentsMargins(6, 0, 0, 0)
        lay.setSpacing(12)

        # ── Tabla de episodios ──
        grp_eps = QGroupBox("Episodes")
        eps_lay = QVBoxLayout(grp_eps)

        self.lbl_anime_nombre = QLabel("No anime loaded")
        self.lbl_anime_nombre.setStyleSheet(
            f"color: {COLOR_DIM}; font-size: 14px; font-weight: 600; padding: 2px 0; letter-spacing: 0.3px;"
        )
        eps_lay.addWidget(self.lbl_anime_nombre)

        self.tabla = QTableWidget(0, 3)
        self.tabla.setHorizontalHeaderLabels(["Ep.", "Title", "Status"])
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.tabla.setColumnWidth(0, 55)
        self.tabla.setColumnWidth(2, 90)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setStyleSheet(
            self.tabla.styleSheet() +
            f"QTableWidget {{ alternate-background-color: {COLOR_CARD}; }}"
        )
        eps_lay.addWidget(self.tabla, 1)
        lay.addWidget(grp_eps, 1)

        # ── Log ──
        grp_log = QGroupBox("Log")
        log_lay = QVBoxLayout(grp_log)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(180)
        log_lay.addWidget(self.log_text)

        btn_clear = QPushButton("Clear log")
        btn_clear.setFixedWidth(110)
        btn_clear.clicked.connect(self.log_text.clear)
        log_lay.addWidget(btn_clear, alignment=Qt.AlignmentFlag.AlignRight)

        lay.addWidget(grp_log)
        return widget

    def _build_bottom_bar(self):
        frame = QFrame()
        frame.setFixedHeight(28)
        lay = QHBoxLayout(frame)
        lay.setContentsMargins(0, 0, 0, 0)
        self.lbl_estado = QLabel("Ready")
        self.lbl_estado.setStyleSheet(f"color: {COLOR_SUBTEXT}; font-size: 11px; letter-spacing: 0.3px;")
        lay.addWidget(self.lbl_estado)
        lay.addStretch()
        lbl_credits = QLabel("jkanime.net")
        lbl_credits.setStyleSheet(f"color: {COLOR_SUBTEXT}; font-size: 10px; letter-spacing: 1px;")
        lay.addWidget(lbl_credits)
        return frame

    # ── Logic ────────────────────────────────────────────────────────────────
    def _status(self, msg: str):
        self.lbl_estado.setText(msg)
        self.statusBar().showMessage(msg)

    def _log(self, msg: str):
        self.log_text.append(f"<span style='color:#555'>{msg}</span>")
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )

    def _elegir_carpeta(self):
        carpeta = QFileDialog.getExistingDirectory(
            self, "Select download folder",
            self.inp_carpeta.text() or os.path.expanduser("~"),
        )
        if carpeta:
            self.inp_carpeta.setText(carpeta)

    @staticmethod
    def _slug_from_input(text: str) -> str:
        """Extrae el slug del anime tanto de una URL completa como de un slug directo."""
        import re
        text = text.strip().rstrip("/")
        # URL completa: https://jkanime.net/nombre-anime o variantes
        match = re.search(r'jkanime\.net/([^/?#]+)', text)
        if match:
            return match.group(1)
        # Ya es un slug (sin dominio)
        return text.lstrip("/")

    def _buscar(self):
        slug = self._slug_from_input(self.inp_slug.text())
        if not slug:
            self._log("⚠ Paste the anime URL.")
            return

        self.btn_buscar.setEnabled(False)
        self.btn_descargar.setEnabled(False)
        self.tabla.setRowCount(0)
        self.episodios = []
        self._log(f"Searching: {slug} …")
        self._status("Searching episodes…")

        self.downloader = JKAnimeDownloader()
        worker = BuscarWorker(self.downloader, slug)
        worker.log_signal.connect(self._log)
        worker.episodios_signal.connect(self._on_episodios_cargados)
        worker.error_signal.connect(self._on_error_busqueda)
        worker.finished.connect(lambda: self.btn_buscar.setEnabled(True))
        self._buscar_worker = worker
        worker.start()

    def _on_episodios_cargados(self, info: dict, episodios: list):
        self.info_anime = info
        self.episodios  = episodios
        nombre = info.get("nombre", info["slug"])
        self.lbl_anime_nombre.setText(nombre)
        self.lbl_anime_nombre.setStyleSheet(
            f"color: {COLOR_TEXT}; font-size: 14px; font-weight: 600; padding: 2px 0; letter-spacing: 0.3px;"
        )
        self._status(f"{nombre} — {len(episodios)} episodes loaded.")
        self._log(f"<span style='color:{COLOR_SUCCESS}'>✓ {len(episodios)} episodios encontrados.</span>")

        self.tabla.setRowCount(len(episodios))
        for i, ep in enumerate(episodios):
            self.tabla.setItem(i, 0, self._cell(str(ep["number"]), center=True))
            self.tabla.setItem(i, 1, self._cell(ep["title"]))
            self.tabla.setItem(i, 2, self._cell("–", center=True))
        self.tabla.resizeRowsToContents()

        # Update spin with actual max
        total = episodios[-1]["number"] if episodios else 1
        self.spin_inicio.setRange(1, total)
        self.spin_fin.setRange(0, total)
        self.bar_episodios.setMaximum(len(episodios))
        self.bar_episodios.setValue(0)

        self.btn_descargar.setEnabled(True)

    def _on_error_busqueda(self, msg: str):
        self._log(f"<span style='color:{COLOR_ERROR}'>✖ Error: {msg}</span>")
        self._status("Search error.")

    def _iniciar_descarga(self):
        if not self.episodios:
            return

        slug    = self._slug_from_input(self.inp_slug.text())
        inicio  = self.spin_inicio.value()
        fin     = self.spin_fin.value() or None
        servidor = self.combo_servidor.currentText()
        carpeta  = self.inp_carpeta.text().strip() or "."

        self.btn_descargar.setEnabled(False)
        self.btn_cancelar.setEnabled(True)
        self.btn_buscar.setEnabled(False)
        self.bar_episodios.setValue(0)
        self.bar_bytes.setVisible(False)
        self._log(f"\n▶ Iniciando descarga de <b style='color:{COLOR_ACCENT2}'>{self.info_anime.get('nombre', slug)}</b> "
                  f"ep {inicio}–{fin or 'last'} (server: {servidor})")
        self._status("Downloading…")

        # Resetear estados en tabla
        for i in range(self.tabla.rowCount()):
            self.tabla.setItem(i, 2, self._cell("–", center=True))

        self.downloader = JKAnimeDownloader()
        # Reusar el CSRF token ya obtenido
        self.downloader.csrf_token = JKAnimeDownloader().csrf_token

        worker = DescargaWorker(self.downloader, slug, inicio, fin, servidor, carpeta)
        worker.log_signal.connect(self._log)
        worker.episodio_signal.connect(self._on_episodio_inicio)
        worker.done_signal.connect(self._on_episodio_done)
        worker.progreso_signal.connect(self._on_progreso)
        worker.finished_signal.connect(self._on_descarga_finalizada)
        worker.error_signal.connect(self._on_error_descarga)
        self._worker = worker
        worker.start()

    def _cancelar_descarga(self):
        if self._worker and self.downloader:
            self.downloader.cancelar()
            self._log(f"<span style='color:{COLOR_ACCENT2}'>⏹ Cancelling…</span>")
            self._status("Cancelling…")
            self.btn_cancelar.setEnabled(False)

    def _on_episodio_inicio(self, actual: int, total: int, titulo: str):
        self.bar_episodios.setMaximum(total)
        self.bar_episodios.setValue(actual - 1)
        self.lbl_ep_actual.setText(f"Downloading: {titulo}")
        self._status(f"Ep {actual}/{total}: {titulo}")
        self.bar_bytes.setValue(0)
        self.bar_bytes.setVisible(False)

    def _on_episodio_done(self, numero_ep: int, exito: bool):
        self.bar_episodios.setValue(self.bar_episodios.value() + 1)
        # Actualizar estado en la tabla
        for i in range(self.tabla.rowCount()):
            item = self.tabla.item(i, 0)
            if item and item.text() == str(numero_ep):
                estado = self._cell("✓ OK" if exito else "✖ Failed", center=True)
                estado.setForeground(
                    QColor(COLOR_SUCCESS) if exito else QColor(COLOR_ERROR)
                )
                self.tabla.setItem(i, 2, estado)
                self.tabla.scrollToItem(self.tabla.item(i, 0))
                break

    def _on_progreso(self, descargado: int, total: int):
        self.bar_bytes.setVisible(True)
        self.bar_bytes.setMaximum(total)
        self.bar_bytes.setValue(descargado)
        mb_d = descargado / 1024 / 1024
        mb_t = total / 1024 / 1024
        self.bar_bytes.setFormat(f"Direct download: {mb_d:.1f} / {mb_t:.1f} MB  (%p%)")

    def _on_descarga_finalizada(self):
        self.btn_descargar.setEnabled(True)
        self.btn_cancelar.setEnabled(False)
        self.btn_buscar.setEnabled(True)
        self.lbl_ep_actual.setText("Download complete.")
        self._status("Download complete.")
        self._log(f"<span style='color:{COLOR_SUCCESS}'>✓ Proceso completado.</span>")

    def _on_error_descarga(self, msg: str):
        self._log(f"<span style='color:{COLOR_ERROR}'>✖ {msg}</span>")
        self._status("Download error.")
        self.btn_descargar.setEnabled(True)
        self.btn_cancelar.setEnabled(False)
        self.btn_buscar.setEnabled(True)

    @staticmethod
    def _cell(text: str, center: bool = False) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        if center:
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        return item


# ── Punto de entrada ──────────────────────────────────────────────────────────
def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Paleta oscura premium
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window,          QColor(COLOR_BG))
    palette.setColor(QPalette.ColorRole.WindowText,      QColor(COLOR_TEXT))
    palette.setColor(QPalette.ColorRole.Base,            QColor(COLOR_PANEL))
    palette.setColor(QPalette.ColorRole.AlternateBase,   QColor(COLOR_CARD))
    palette.setColor(QPalette.ColorRole.ToolTipBase,     QColor(COLOR_CARD))
    palette.setColor(QPalette.ColorRole.ToolTipText,     QColor(COLOR_TEXT))
    palette.setColor(QPalette.ColorRole.Text,            QColor(COLOR_TEXT))
    palette.setColor(QPalette.ColorRole.Button,          QColor(COLOR_CARD))
    palette.setColor(QPalette.ColorRole.ButtonText,      QColor(COLOR_TEXT))
    palette.setColor(QPalette.ColorRole.BrightText,      QColor(COLOR_ACCENT2))
    palette.setColor(QPalette.ColorRole.Highlight,       QColor(COLOR_ACCENT2))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#000000"))
    palette.setColor(QPalette.ColorRole.Mid,             QColor(COLOR_ELEVATED))
    palette.setColor(QPalette.ColorRole.Dark,            QColor(COLOR_BORDER))
    palette.setColor(QPalette.ColorRole.Shadow,          QColor("#000000"))
    app.setPalette(palette)

    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
