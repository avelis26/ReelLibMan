"""
ReelLibMan file system scanner.

Reads movie library paths from config/settings.json and scans
for media folders and files.

Usage:
    Not called directly — imported and called by gui/main_window.py.
"""

import os
import json
import re

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "../config/settings.json")


def load_config() -> dict:
    """Load and return the settings.json config file."""
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


def scan_movies() -> list[dict]:
    """
    Scan all configured movie library paths for media folders.

    Returns:
        list[dict]: Each entry contains folder_name, folder_path,
                    tmdb_id (if found in folder name), and media_file path.
    """
    config = load_config()
    paths = config["library"]["movie_paths"]
    extensions = config["file_extensions"]
    movies = []

    for root_path in paths:
        if not os.path.exists(root_path):
            continue
        for folder in sorted(os.scandir(root_path), key=lambda e: e.name.lower()):
            if not folder.is_dir():
                continue

            tmdb_id = None
            match = re.search(r'\[(\d+)\]', folder.name)
            if match:
                tmdb_id = match.group(1)

            media_file = None
            try:
                for f in os.scandir(folder.path):
                    if any(f.name.lower().endswith(ext) for ext in extensions):
                        media_file = f.path
                        break
            except PermissionError:
                pass

            movies.append({
                "folder_name": folder.name,
                "folder_path": folder.path,
                "tmdb_id": tmdb_id,
                "media_file": media_file
            })

    return movies


if __name__ == "__main__":
    results = scan_movies()
    print(f"Found {len(results)} movies:")
    for m in results:
        print(f"  {m['folder_name']} — TMDB ID: {m['tmdb_id']} — File: {m['media_file']}")