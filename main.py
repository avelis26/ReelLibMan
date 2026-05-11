"""
ReelLibMan main entry point.

Orchestrates the movie metadata fetch and database insert pipeline.

Usage:
    python main.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from gui.main_window import launch

if __name__ == "__main__":
    launch()
