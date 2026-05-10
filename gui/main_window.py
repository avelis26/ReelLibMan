"""
ReelLibMan main application window.

Provides the primary GUI for searching and fetching movie metadata.

Usage:
    Not called directly — launched by main.py.
"""

import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QLabel, QStatusBar
)
from PyQt6.QtCore import Qt

from api.get_movie_tmdb_api_data import get_movie_by_name
from cache.insert_api_data import save_movie


class MainWindow(QMainWindow):
    """Primary application window for ReelLibMan."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ReelLibMan")
        self.setMinimumWidth(500)
        self._build_ui()

    def _build_ui(self):
        """Construct and arrange UI elements."""
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

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

        # Result label
        self.result_label = QLabel("")
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.result_label)

        # Status bar
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Ready")

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

        self.search_btn.setEnabled(True)


def launch():
    """Initialize and launch the PyQt6 application."""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())