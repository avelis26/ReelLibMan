"""
ReelLibMan main application window.

Provides the primary GUI for searching and fetching movie metadata.

Usage:
    Not called directly — launched by main.py.
"""

import os
import sys
import requests
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QLabel, QStatusBar, QSplashScreen
)
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve

from api.get_movie_tmdb_api_data import get_movie_by_name
from cache.insert_api_data import save_movie

ASSETS = os.path.join(os.path.dirname(__file__), "../assets")
ICON_HEIGHT = 48
POSTER_HEIGHT = 144
POSTER_WIDTH = int(POSTER_HEIGHT * 16 / 9)
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/original"


class SplashScreen(QSplashScreen):
    """Splash screen with fade-in and fade-out animations."""

    def __init__(self):
        pixmap = QPixmap(os.path.join(ASSETS, "ReelLibMan_Splash.png"))
        super().__init__(pixmap, Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowOpacity(0.0)
        self._fade_in()

    def _fade_in(self):
        """Fade in over 1 second."""
        self._anim = QPropertyAnimation(self, b"windowOpacity")
        self._anim.setDuration(1000)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self._anim.start()

    def fade_out(self, on_done):
        """Fade out over 2 seconds then call on_done."""
        self._anim = QPropertyAnimation(self, b"windowOpacity")
        self._anim.setDuration(2000)
        self._anim.setStartValue(1.0)
        self._anim.setEndValue(0.0)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self._anim.finished.connect(on_done)
        self._anim.start()


class MainWindow(QMainWindow):
    """Primary application window for ReelLibMan."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ReelLibMan")
        self.setMinimumWidth(600)
        self._set_icon()
        self._build_ui()

    def _set_icon(self):
        """Set the window/taskbar icon."""
        self.setWindowIcon(QIcon(os.path.join(ASSETS, "ReelLibMan_Icon.png")))

    def _build_ui(self):
        """Construct and arrange UI elements."""
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Header row — icon + headline
        header_layout = QHBoxLayout()
        header_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        icon_label = QLabel()
        icon_pixmap = QPixmap(os.path.join(ASSETS, "ReelLibMan_Icon.png"))
        icon_label.setPixmap(icon_pixmap.scaledToHeight(ICON_HEIGHT, Qt.TransformationMode.SmoothTransformation))

        headline_label = QLabel()
        headline_pixmap = QPixmap(os.path.join(ASSETS, "ReelLibMan_Headline.png"))
        headline_label.setPixmap(headline_pixmap.scaledToHeight(ICON_HEIGHT, Qt.TransformationMode.SmoothTransformation))

        header_layout.addWidget(icon_label)
        header_layout.addWidget(headline_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Search row
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter movie title...")
        self.search_input.returnPressed.connect(self._on_search)

        self.search_btn = QPushButton("Search")
        self.search_btn.clicked.connect(self._on_search)

        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_btn)
        layout.addLayout(search_layout)

        # Poster panel
        self.poster_panel = QHBoxLayout()
        self.poster_panel.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.poster_placeholder = QLabel()
        self.poster_placeholder.setFixedSize(POSTER_WIDTH, POSTER_HEIGHT)
        self.poster_placeholder.setStyleSheet("background-color: #1a1a2e; border: 1px solid #333;")
        self.poster_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.poster_placeholder.setText("No results yet")
        self.poster_panel.addWidget(self.poster_placeholder)
        layout.addLayout(self.poster_panel)
        self.result_label = QLabel("")
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.result_label)

        # Status bar
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Ready")

    def _load_poster(self, poster_path):
        """Fetch and display the movie poster from TMDB."""
        if not poster_path:
            self.poster_placeholder.setText("No poster available")
            return
        try:
            url = f"{TMDB_IMAGE_BASE}{poster_path}"
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            pixmap = QPixmap()
            pixmap.loadFromData(resp.content)
            self.poster_placeholder.setPixmap(
                pixmap.scaledToHeight(POSTER_HEIGHT, Qt.TransformationMode.SmoothTransformation)
            )
            self.poster_placeholder.setFixedSize(
                pixmap.scaledToHeight(POSTER_HEIGHT, Qt.TransformationMode.SmoothTransformation).width(),
                POSTER_HEIGHT
            )
        except Exception as e:
            self.poster_placeholder.setText("Failed to load poster")
            self.status.showMessage(f"Poster error: {e}")

    def _on_search(self):
        """Fetch metadata and save to DB when search is triggered."""
        title = self.search_input.text().strip()
        if not title:
            self.status.showMessage("Please enter a movie title.")
            return

        self.status.showMessage(f"Searching for: {title}...")
        self.search_btn.setEnabled(False)

        data = get_movie_by_name(title)

        if not data:
            self.result_label.setText("No results found.")
            self.status.showMessage("Search complete — no results.")
        else:
            save_movie(data)
            year = data.get("release_date", "")[:4]
            self.result_label.setText(f"✓ Saved: {data['title']} ({year}) — TMDB ID: {data['id']}")
            self.status.showMessage("Done.")
            self._load_poster(data.get("poster_path"))

        self.search_btn.setEnabled(True)


def launch():
    """Initialize splash, then launch the main window."""
    app = QApplication(sys.argv)

    splash = SplashScreen()
    splash.show()
    app.processEvents()

    # Build main window while splash is visible
    window = MainWindow()

    def show_main():
        splash.finish(window)
        window.show()

    # Wait 1.5s (fade-in completes) then start fade-out into main window
    QTimer.singleShot(1500, lambda: splash.fade_out(show_main))

    sys.exit(app.exec())