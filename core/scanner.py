"""
ReelLibMan file system scanner.

Reads movie library paths from config/settings.json and scans
for media folders and files. No API or online source involvement —
this script only deals with the local file system.

Usage:
    Not called directly — imported and called by gui/main_window.py.
"""

import os
import json

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
                    media_file (filename only), and media_file_path (full path).
    """
    config = load_config()
    paths = config["library"]["movie_paths"]
    extensions = config["file_extensions"]
    ignore_suffixes = config.get("ignore_suffixes", [])
    movies = []

    for root_path in paths:
        if not os.path.exists(root_path):
            continue
        for folder in sorted(os.scandir(root_path), key=lambda e: e.name.lower()):
            if not folder.is_dir():
                continue

            media_file = None
            media_file_path = None
            try:
                for f in os.scandir(folder.path):
                    name_no_ext = os.path.splitext(f.name)[0].lower()
                    if not any(f.name.lower().endswith(ext) for ext in extensions):
                        continue
                    if any(name_no_ext.endswith(s.lower()) for s in ignore_suffixes):
                        continue
                    media_file = f.name
                    media_file_path = f.path
                    break
            except PermissionError:
                pass

            movies.append({
                "folder_name": folder.name,
                "folder_path": folder.path,
                "media_file": media_file,
                "media_file_path": media_file_path
            })

    return movies


if __name__ == "__main__":
    results = scan_movies()
    print(f"Found {len(results)} movies:")
    for m in results:
        print(f"  {m['folder_name']} — File: {m['media_file']}")