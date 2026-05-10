"""
ReelLibMan main entry point.

Orchestrates the movie metadata fetch and database insert pipeline.

Usage:
    python main.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from api.get_movie_tmdb_api_data import get_movie_by_name
from cache.insert_api_data import save_movie

# --- Hardcoded for dev ---
MOVIE_TITLE = "3 Ninjas"
# ------------------------

if __name__ == "__main__":
    print(f"Fetching metadata for: {MOVIE_TITLE}")
    data = get_movie_by_name(MOVIE_TITLE)

    if not data:
        print("No results found.")
        sys.exit(1)

    save_movie(data)