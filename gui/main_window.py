"""
ReelLibMan main application window.

Provides the primary GUI shell for ReelLibMan.

Usage:
    Not called directly — launched by main.py.
"""

import os
import sys
import time
import threading
import requests
from io import BytesIO
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QLabel, QStatusBar, QSplashScreen,
    QSizePolicy, QScrollArea, QFrame,
    QTextEdit, QGridLayout, QProgressBar,
    QSplitter, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtGui import QPixmap, QIcon, QFont
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal, QEvent
from PyQt6.QtCore import QObject
from core.scanner import scan_movies
from api.get_movie_tmdb_api_data import search_movies_brief, parse_title_and_year

ASSETS = os.path.join(os.path.dirname(__file__), "../assets")
ICON_HEIGHT = 65
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/original"

NAV_BUTTONS = [
    ("Scan\nFile\nSystem",          "#B2BEB5", "#00ccff"),
    ("Scrape\nWeb\nAPI",            "#B2BEB5", "#00ff99"),
    ("Manually\nEdit\nMetadata",    "#B2BEB5", "#ff9900"),
    ("Move\nAnd\nRename\nFiles",    "#B2BEB5", "#ff66cc"),
]
NAV_BUTTONS_BOTTOM = [
    ("Check\nFor\nUpdates",         "#B2BEB5", "#aaaaff"),
    ("Settings",                    "#B2BEB5", "#ffff66"),
    ("Quit",                        "#B2BEB5", "#ff4444"),
]

COLOR_FS     = "#00ccff"
COLOR_SCRAPE = "#00ff99"


class SplashScreen(QSplashScreen):
    def __init__(self):
        pixmap = QPixmap(os.path.join(ASSETS, "1.png"))
        super().__init__(pixmap, Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowOpacity(0.0)
        self._fade_in()

    def _fade_in(self):
        self._anim = QPropertyAnimation(self, b"windowOpacity")
        self._anim.setDuration(1000)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self._anim.start()

    def fade_out(self, on_done):
        self._anim = QPropertyAnimation(self, b"windowOpacity")
        self._anim.setDuration(2000)
        self._anim.setStartValue(1.0)
        self._anim.setEndValue(0.0)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self._anim.finished.connect(on_done)
        self._anim.start()


def _nav_btn(label, color, border_color):
    btn = QPushButton(label)
    btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    btn.setStyleSheet(f"""
        QPushButton {{
            color: {color};
            border: 1px solid {border_color};
            padding: 6px;
            text-align: center;
            background-color: #12122a;
        }}
        QPushButton:hover {{
            background-color: #1e1e3a;
        }}
    """)
    return btn


class _WorkerSignals(QObject):
    done  = pyqtSignal(list)
    error = pyqtSignal(str)


class MainWindow(QMainWindow):
    """Primary application window for ReelLibMan."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ReelLibMan")
        self.setMinimumSize(1280, 720)
        self.setWindowIcon(QIcon(os.path.join(ASSETS, "1.png")))
        self._scan_results = []
        self._fs_search_matches = []   # rows matching the current query
        self._fs_search_idx = -1       # index into _fs_search_matches
        self._build_ui()
        self.showMaximized()

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ── TOP BAR ──────────────────────────────────────────────────────────
        top_bar = QWidget()
        top_bar.setFixedHeight(80)
        top_bar.setStyleSheet("background-color: #1a1a2e;")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(10, 5, 10, 5)

        icon_lbl = QLabel()
        icon_pix = QPixmap(os.path.join(ASSETS, "1.png"))
        icon_lbl.setPixmap(icon_pix.scaledToHeight(ICON_HEIGHT, Qt.TransformationMode.SmoothTransformation))
        headline_lbl = QLabel()
        headline_pix = QPixmap(os.path.join(ASSETS, "2.png"))
        headline_lbl.setPixmap(headline_pix.scaledToHeight(ICON_HEIGHT, Qt.TransformationMode.SmoothTransformation))
        version_lbl = QLabel("v1.0.0 - GIT")
        version_lbl.setStyleSheet("color: #888; font-size: 11px;")
        version_lbl.setAlignment(Qt.AlignmentFlag.AlignBottom)

        brand_inner = QHBoxLayout()
        brand_inner.addWidget(icon_lbl)
        brand_inner.addWidget(headline_lbl)
        brand_inner.addWidget(version_lbl)
        brand_inner.addStretch()
        top_layout.addLayout(brand_inner)

        self.btn_movies = QPushButton("🎬  MOVIES")
        self.btn_movies.setFixedSize(300, 56)
        self.btn_movies.setStyleSheet("font-size: 15px; font-weight: bold;")
        self.btn_tv = QPushButton("📺  TV SHOWS")
        self.btn_tv.setFixedSize(300, 56)
        self.btn_tv.setStyleSheet("font-size: 15px; font-weight: bold;")
        top_layout.addWidget(self.btn_movies)
        top_layout.addWidget(self.btn_tv)

        self.activity_log = QTextEdit()
        self.activity_log.setReadOnly(True)
        self.activity_log.setStyleSheet("background-color: #0d0d1a; color: #00ff99; font-family: monospace; font-size: 11px;")
        self.activity_log.setPlaceholderText("App activity will appear here...")
        top_layout.addWidget(self.activity_log, 1)

        root_layout.addWidget(top_bar)

        # ── MIDDLE + DETAIL VERTICAL SPLITTER ────────────────────────────────
        v_splitter = QSplitter(Qt.Orientation.Vertical)
        v_splitter.setChildrenCollapsible(False)

        # ── MIDDLE ROW ───────────────────────────────────────────────────────
        middle = QWidget()
        middle_layout = QHBoxLayout(middle)
        middle_layout.setContentsMargins(0, 0, 0, 0)
        middle_layout.setSpacing(0)

        # ── LEFT NAV ─────────────────────────────────────────────────────────
        nav = QWidget()
        nav.setFixedWidth(110)
        nav.setStyleSheet("background-color: #12122a;")
        nav_layout = QVBoxLayout(nav)
        nav_layout.setContentsMargins(5, 10, 5, 10)
        nav_layout.setSpacing(4)

        nav_actions = {
            "Scan\nFile\nSystem": self._on_scan,
            "Scrape\nWeb\nAPI":   self._on_scrape,
            "Quit":               self._on_quit,
        }
        for label, color, border_color in NAV_BUTTONS:
            btn = _nav_btn(label, color, border_color)
            if label in nav_actions:
                btn.clicked.connect(nav_actions[label])
            nav_layout.addWidget(btn)

        nav_layout.addStretch()

        for label, color, border_color in NAV_BUTTONS_BOTTOM:
            btn = _nav_btn(label, color, border_color)
            if label in nav_actions:
                btn.clicked.connect(nav_actions[label])
            nav_layout.addWidget(btn)

        middle_layout.addWidget(nav)

        # ── MAIN CONTENT SPLITTER (horizontal) ───────────────────────────────
        h_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel — file system list
        left_panel = QFrame()
        left_panel.setStyleSheet(f"border: 2px solid {COLOR_FS};")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(8, 8, 8, 8)
        left_layout.setSpacing(6)

        fs_search_row = QHBoxLayout()
        self.fs_search_input = QLineEdit()
        self.fs_search_input.setPlaceholderText("File system search box")
        self.fs_search_input.returnPressed.connect(self._on_fs_search)
        self.fs_search_input.textChanged.connect(self._on_fs_search_reset)
        self.fs_search_input.installEventFilter(self)
        fs_search_btn = QPushButton("Search")
        fs_search_btn.clicked.connect(self._on_fs_search)
        fs_search_row.addWidget(self.fs_search_input)
        fs_search_row.addWidget(fs_search_btn)
        left_layout.addLayout(fs_search_row)

        self.file_list = QTableWidget()
        self.file_list.setColumnCount(4)
        self.file_list.setStyleSheet("border: 1px solid #444;")
        self.file_list.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.file_list.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.file_list.verticalHeader().setVisible(True)
        self.file_list.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.file_list.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.file_list.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.file_list.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.file_list.setColumnWidth(1, 36)
        self.file_list.setColumnWidth(2, 36)
        self.file_list.setColumnWidth(3, 36)
        self.file_list.horizontalHeader().setStyleSheet("""
            QHeaderView::section {
                background-color: #1a1a2e;
                color: #cccccc;
                border: 1px solid #333;
                padding: 4px;
            }
        """)

        self.file_list.setHorizontalHeaderItem(0, QTableWidgetItem("File Name"))

        header_specs = [
            (1, "🟢", "Matched"),
            (2, "🟠", "Edited"),
            (3, "🟣", "Organized"),
        ]
        for col, symbol, tip in header_specs:
            item = QTableWidgetItem(symbol)
            item.setToolTip(tip)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item.setFont(QFont("Arial", 18))
            self.file_list.setHorizontalHeaderItem(col, item)

        self.file_list.itemClicked.connect(lambda item: self._on_file_selected(item) if item else None)
        self.file_list.currentItemChanged.connect(lambda current, _: self._on_file_selected(current) if current else None)
        left_layout.addWidget(self.file_list)
        h_splitter.addWidget(left_panel)

        # Right panel — scrape results
        right_panel = QFrame()
        right_panel.setStyleSheet(f"border: 2px solid {COLOR_SCRAPE};")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(8, 8, 8, 8)
        right_layout.setSpacing(6)

        updates_lbl = QLabel("App updates from app author could be displayed here")
        updates_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        updates_lbl.setStyleSheet("border: 1px solid #333; padding: 4px; color: #888;")
        right_layout.addWidget(updates_lbl)

        manual_search_row = QHBoxLayout()
        self.manual_search_input = QLineEdit()
        self.manual_search_input.setPlaceholderText("Manual movie title search box")
        self.manual_search_input.setStyleSheet("border: 1px solid #555;")
        manual_search_btn = QPushButton("Search")
        manual_search_btn.clicked.connect(self._on_search)
        self.manual_search_input.returnPressed.connect(self._on_search)
        manual_search_row.addWidget(self.manual_search_input)
        manual_search_row.addWidget(manual_search_btn)
        right_layout.addLayout(manual_search_row)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        self.poster_grid_widget = QWidget()
        self.poster_grid = QGridLayout(self.poster_grid_widget)
        self.poster_grid.setSpacing(6)
        self._populate_placeholder_posters(8)
        scroll.setWidget(self.poster_grid_widget)
        right_layout.addWidget(scroll)

        action_row = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("Progress bar and HTTP API call status display")
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rollback_btn = QPushButton("Rollback")
        accept_btn = QPushButton("Accept / Write Changes")
        action_row.addWidget(self.progress_bar, 3)
        action_row.addWidget(rollback_btn, 1)
        action_row.addWidget(accept_btn, 1)
        right_layout.addLayout(action_row)

        h_splitter.addWidget(right_panel)
        h_splitter.setSizes([400, 900])
        middle_layout.addWidget(h_splitter)

        v_splitter.addWidget(middle)

        # ── DETAIL PANEL ─────────────────────────────────────────────────────
        detail = QWidget()
        detail.setStyleSheet("background-color: #12122a; border-top: 1px solid #333;")
        detail_layout = QHBoxLayout(detail)
        detail_layout.setContentsMargins(8, 8, 8, 8)
        detail_layout.setSpacing(8)

        self.detail_poster = QLabel("Movie\nPoster")
        self.detail_poster.setFixedWidth(300)
        self.detail_poster.setMinimumHeight(370)
        self.detail_poster.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self.detail_poster.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.detail_poster.setStyleSheet("background-color: #1a1a2e; border: 1px solid #333;")
        detail_layout.addWidget(self.detail_poster)

        detail_right = QVBoxLayout()
        self.detail_filename = QLabel("File name of selected movie")
        self.detail_filename.setStyleSheet("color: #ccc; font-weight: bold;")
        self.detail_filepath = QLabel("Full file system path of selected movie file")
        self.detail_filepath.setStyleSheet("color: #888; font-size: 11px;")
        detail_right.addWidget(self.detail_filename)
        detail_right.addWidget(self.detail_filepath)

        self.detail_metadata = QTextEdit()
        self.detail_metadata.setReadOnly(True)
        self.detail_metadata.setPlaceholderText("Metadata of selected movie will appear here (NFO). Click 'Manually Edit Metadata' to edit.")
        self.detail_metadata.setStyleSheet("background-color: #0d0d1a; color: #ccc; font-size: 11px; border: 1px solid #333;")
        detail_right.addWidget(self.detail_metadata)

        self.detail_art = QLabel("Additional art: banner, clearlogo, fanart — displayed here if found on file system")
        self.detail_art.setFixedHeight(90)
        self.detail_art.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.detail_art.setStyleSheet("background-color: #1a1a2e; border: 1px solid #333; color: #888; font-size: 11px;")
        detail_right.addWidget(self.detail_art)

        detail_layout.addLayout(detail_right)
        v_splitter.addWidget(detail)

        v_splitter.setStretchFactor(0, 11)
        v_splitter.setStretchFactor(1, 9)

        root_layout.addWidget(v_splitter, 1)

        # ── STATUS BAR ───────────────────────────────────────────────────────
        self.status = QStatusBar()
        self.status.setStyleSheet("font-size: 11px; color: #888;")
        self.setStatusBar(self.status)
        self.status.showMessage("Ready  |  CPU: --  |  RAM: --  |  Storage: --  |  DB: --  |  API Calls: 0  |  Internet: --")

    # ── HELPERS ──────────────────────────────────────────────────────────────

    def _populate_placeholder_posters(self, count):
        """Fill poster grid with placeholder tiles."""
        for i in range(count):
            tile = QWidget()
            tile_layout = QVBoxLayout(tile)
            tile_layout.setSpacing(2)
            img = QLabel(f"Scrape Result {i+1:02d}\nPoster Image")
            img.setFixedSize(140, 200)
            img.setAlignment(Qt.AlignmentFlag.AlignCenter)
            img.setStyleSheet("background-color: #1a1a2e; border: 1px solid #444; color: #888; font-size: 10px;")
            meta = QLabel(f"Scrape Result {i+1:02d}\nMetadata")
            meta.setAlignment(Qt.AlignmentFlag.AlignCenter)
            meta.setStyleSheet("color: #888; font-size: 10px;")
            tile_layout.addWidget(img)
            tile_layout.addWidget(meta)
            self.poster_grid.addWidget(tile, 0, i)

    def _clear_poster_grid(self):
        """Remove all widgets from the poster grid."""
        while self.poster_grid.count():
            item = self.poster_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _make_result_tile(self, result):
        """Build a single grid tile for one TMDB search result."""
        tile = QWidget()
        tile_layout = QVBoxLayout(tile)
        tile_layout.setSpacing(4)
        tile_layout.setContentsMargins(4, 4, 4, 4)

        poster_lbl = QLabel("Loading…")
        poster_lbl.setFixedSize(210, 300)
        poster_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        poster_lbl.setStyleSheet(
            "background-color: #1a1a2e; border: 1px solid #444; color: #888; font-size: 10px;"
        )

        overview = result.get("overview", "")
        short_plot = (overview[:117] + "…") if len(overview) > 120 else overview

        meta_text = (
            f"<b>{result['title']}</b><br>"
            f"{result['release_year']}<br>"
            f"<small>{short_plot}</small>"
        )
        meta_lbl = QLabel(meta_text)
        meta_lbl.setWordWrap(True)
        meta_lbl.setFixedWidth(210)
        meta_lbl.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        meta_lbl.setStyleSheet("color: #ccc; font-size: 18px;")

        tile_layout.addWidget(poster_lbl)
        tile_layout.addWidget(meta_lbl)
        return tile, poster_lbl

    def _fetch_poster_async(self, poster_url, poster_lbl):
        """Download a TMDB poster in a background thread and update the label."""
        sig = _WorkerSignals()
        sig.done.connect(lambda _: None)   # unused slot, keeps sig alive

        class _PosterSignals(QObject):
            ready = pyqtSignal(bytes)
            fail  = pyqtSignal()

        ps = _PosterSignals()
        ps.ready.connect(lambda data: self._apply_poster(poster_lbl, data))
        ps.fail.connect(lambda: poster_lbl.setText("No\nImage"))

        def worker():
            try:
                resp = requests.get(poster_url, timeout=10)
                resp.raise_for_status()
                ps.ready.emit(resp.content)
            except Exception:
                ps.fail.emit()

        threading.Thread(target=worker, daemon=True).start()
        self._poster_signals = getattr(self, "_poster_signals", [])
        self._poster_signals.append(ps)

    def _apply_poster(self, poster_lbl, data):
        pix = QPixmap()
        pix.loadFromData(data)
        if not pix.isNull():
            scaled = pix.scaled(
                210, 300,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            poster_lbl.setPixmap(scaled)
            poster_lbl.setText("")
        else:
            poster_lbl.setText("No\nImage")

    def _populate_scrape_results(self, results):
        """Clear the grid and fill it with live TMDB search results."""
        self._clear_poster_grid()
        if not results:
            lbl = QLabel("No results found.")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("color: #888;")
            self.poster_grid.addWidget(lbl, 0, 0)
            return

        for col, result in enumerate(results):
            tile, poster_lbl = self._make_result_tile(result)
            self.poster_grid.addWidget(tile, 0, col)
            if result.get("poster_url"):
                self._fetch_poster_async(result["poster_url"], poster_lbl)
            else:
                poster_lbl.setText("No\nPoster")

    def _clear_poster(self, msg="Movie\nPoster"):
        """Reset the detail poster label to a text placeholder."""
        self.detail_poster.clear()
        self.detail_poster.setText(msg)

    def log(self, msg):
        """Append a message to the activity log."""
        self.activity_log.append(f"> {msg}")

    # ── SLOT HANDLERS ────────────────────────────────────────────────────────

    def eventFilter(self, obj, event):
        """Clear the fs search box when ESC is pressed inside it."""
        if obj is self.fs_search_input and event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Escape:
                self.fs_search_input.clear()
                # textChanged fires automatically, resetting the cycle
                return True
        return super().eventFilter(obj, event)

    def _on_fs_search_reset(self):
        """Called whenever the query text changes — invalidates the current match cycle."""
        self._fs_search_matches = []
        self._fs_search_idx = -1

    def _on_fs_search(self):
        """Cycle through rows whose File Name contains the query, one per Enter/click."""
        query = self.fs_search_input.text().strip().lower()

        for row in range(self.file_list.rowCount()):
            self.file_list.setRowHidden(row, False)

        if not query:
            self.file_list.clearSelection()
            return

        # Build match list only at the start of a fresh search cycle
        if not self._fs_search_matches:
            self._fs_search_matches = [
                row for row in range(self.file_list.rowCount())
                if (item := self.file_list.item(row, 0)) and query in item.text().lower()
            ]
            self._fs_search_idx = -1

        if not self._fs_search_matches:
            self.file_list.clearSelection()
            self.status.showMessage(f'No match found for "{self.fs_search_input.text().strip()}"')
            return

        # Advance to next match, wrapping around
        self._fs_search_idx = (self._fs_search_idx + 1) % len(self._fs_search_matches)
        row = self._fs_search_matches[self._fs_search_idx]
        self.file_list.clearSelection()
        self.file_list.selectRow(row)
        self.file_list.scrollToItem(
            self.file_list.item(row, 0),
            QTableWidget.ScrollHint.PositionAtTop,
        )
        n = len(self._fs_search_matches)
        i = self._fs_search_idx + 1
        self.status.showMessage(f'Match {i} of {n} for "{self.fs_search_input.text().strip()}"')

    def _on_scan(self):
        """Scan the file system and populate the file list."""
        self.file_list.setRowCount(0)
        self.log("Scanning file system...")
        self._scan_results = scan_movies()
        for m in self._scan_results:
            try:
                if not m.get("media_file", "").strip():
                    continue
                row = self.file_list.rowCount()
                self.file_list.insertRow(row)
                self.file_list.setItem(row, 0, QTableWidgetItem(m["media_file"]))
                for col in (1, 2, 3):
                    self.file_list.setItem(row, col, QTableWidgetItem(""))
            except Exception as e:
                self.log(f"FAILED: {m['folder_name']} | {e}")
        self.log(f"Scan complete — {len(self._scan_results)} movie folders found.")
        self.status.showMessage(f"Scan complete — {len(self._scan_results)} movies found.")

    def _on_file_selected(self, item):
        """Display poster and NFO for the selected movie file, if they exist."""
        media_file = self.file_list.item(item.row(), 0).text()

        folder = None
        for m in self._scan_results:
            if m.get("media_file") == media_file:
                folder = m.get("folder_path") or os.path.dirname(m.get("media_file", ""))
                break

        if not folder:
            folder = os.path.dirname(media_file)

        self.detail_filename.setText(os.path.basename(media_file))
        self.detail_filepath.setText(folder)

        # Search for a poster image
        poster_path = None
        for name in ("poster.jpg", "poster.jpeg", "poster.png"):
            candidate = os.path.join(folder, name)
            if os.path.isfile(candidate):
                poster_path = candidate
                break

        # Load NFO metadata
        nfo_path = None
        for name in (os.path.splitext(os.path.basename(media_file))[0] + ".nfo", "movie.nfo"):
            candidate = os.path.join(folder, name)
            if os.path.isfile(candidate):
                nfo_path = candidate
                break

        if nfo_path:
            try:
                with open(nfo_path, "r", encoding="utf-8", errors="replace") as f:
                    self.detail_metadata.setPlainText(f.read())
            except Exception as e:
                self.detail_metadata.clear()
                self.detail_metadata.setPlaceholderText(f"(could not read NFO: {e})")
        else:
            self.detail_metadata.clear()

        if poster_path:
            pix = QPixmap(poster_path)
            if not pix.isNull():
                scaled = pix.scaled(
                    self.detail_poster.width(),
                    self.detail_poster.height(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self.detail_poster.setPixmap(scaled)
                self.detail_poster.setText("")
            else:
                self._clear_poster("(could not load\nposter image)")
                self.log(f"WARNING: QPixmap failed to load {poster_path}")
        else:
            self._clear_poster("No poster\nfound")

    def _on_scrape(self):
        """Scrape TMDB for the currently selected movie."""
        manual = self.manual_search_input.text().strip()

        selected_items = self.file_list.selectedItems()
        if selected_items:
            media_file = self.file_list.item(selected_items[0].row(), 0).text()
            title, year = parse_title_and_year(os.path.basename(media_file))
        elif manual:
            title, year = manual, None
        else:
            self.status.showMessage("Select a movie from the list or enter a title before scraping.")
            return

        # Manual box overrides the parsed title if provided
        if manual:
            title, year = manual, None

        self.log(f"Scraping TMDB for: {title}" + (f" ({year})" if year else ""))
        self.status.showMessage(f"Scraping TMDB for: {title}…")
        self.progress_bar.setFormat("Fetching search results…")
        self.progress_bar.setValue(10)

        signals = _WorkerSignals()
        signals.done.connect(self._on_scrape_done)
        signals.error.connect(self._on_scrape_error)

        def worker():
            try:
                results = search_movies_brief(title, year=year, max_results=8)
                signals.done.emit(list(results))
            except Exception as e:
                import traceback
                traceback.print_exc()
                signals.error.emit(str(e))

        threading.Thread(target=worker, daemon=True).start()

    def _on_scrape_done(self, results):
        self._populate_scrape_results(results)
        self.progress_bar.setValue(100)
        self.progress_bar.setFormat(f"{len(results)} result(s) returned")
        self.log(f"Scrape complete — {len(results)} result(s).")
        self.status.showMessage(f"Scrape complete — {len(results)} result(s).")

    def _on_scrape_error(self, msg):
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("Scrape failed")
        self.log(f"ERROR during scrape: {msg}")
        self.status.showMessage(f"Scrape error: {msg}")

    def _on_quit(self):
        """Cleanly exit the application."""
        QApplication.quit()

    def _on_search(self):
        """Manual search box — triggers a scrape using the typed title."""
        title = self.manual_search_input.text().strip()
        if not title:
            self.status.showMessage("Please enter a movie title.")
            return
        self.log(f"Manual search: {title}")
        self._on_scrape()


# ── ENTRY POINT ──────────────────────────────────────────────────────────────

def launch():
    """Initialize splash, then launch the main window."""
    app = QApplication(sys.argv)

    splash = SplashScreen()
    splash.show()
    app.processEvents()
    time.sleep(1)
    window = MainWindow()

    def show_main():
        splash.finish(window)
        window.show()

    QTimer.singleShot(1500, lambda: splash.fade_out(show_main))

    sys.exit(app.exec())