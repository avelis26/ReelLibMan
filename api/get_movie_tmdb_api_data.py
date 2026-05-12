"""
TMDB API client for ReelLibMan.

Provides functions to fetch movie metadata from the TMDB API.

- search_movies_brief()  : returns 4-8 results with poster/title/year/plot for the scrape grid
- get_full_movie_by_id() : fetches complete metadata for DB storage (renamed from get_movie_by_id)
- get_full_movie_by_name(): fetches complete metadata by title (renamed from get_movie_by_name)

Usage:
    python get_movie_tmdb_api_data.py --tmdb_id 16314
    python get_movie_tmdb_api_data.py --movie_title "3 Ninjas"
"""

import os
import re
import json
import requests
import argparse
from dotenv import load_dotenv

load_dotenv()

API_KEY  = os.getenv("TMDB_API_KEY")
BASE_URL = "https://api.themoviedb.org/3"
APPEND   = "credits,release_dates,keywords,images,external_ids"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w342"   # w342 is plenty for grid tiles


# ── FILENAME PARSING ─────────────────────────────────────────────────────────

def parse_title_and_year(filename):
    """
    Extract a clean title and optional year from a media filename.

    Strips the file extension, replaces underscores/dots with spaces, then
    truncates at the first 4-digit year token, returning everything before it
    as the title and the year itself (or None if not found).

    Examples:
        "Grand_Prix_of_Europe_(2025)_[1316147].mp4" -> ("Grand Prix of Europe", "2025")
        "GOAT:2026.2160p.4K.WEB.x265.mp4"           -> ("GOAT", "2026")
        "Forrest_Gump_(1994)[13].mp4"                -> ("Forrest Gump", "1994")
        "Alien.mp4"                                  -> ("Alien", None)
    """
    name = os.path.splitext(os.path.basename(filename))[0]
    # Normalise separators
    name = name.replace("_", " ").replace(".", " ")
    # Find a 4-digit year (1900-2099)
    m = re.search(r"\b((?:19|20)\d{2})\b", name)
    if m:
        year  = m.group(1)
        title = name[:m.start()].strip(" -([])")
    else:
        year  = None
        title = name.strip()
    return title, year


# ── BRIEF SEARCH (scrape grid) ────────────────────────────────────────────────

def search_movies_brief(title, year=None, max_results=8):
    """
    Search TMDB and return up to *max_results* lightweight dicts suitable for
    displaying in the scrape results grid.

    Each dict contains:
        tmdb_id, title, release_year, overview, poster_url
    """
    params = {"api_key": API_KEY, "query": title}
    if year:
        params["year"] = year

    r = requests.get(f"{BASE_URL}/search/movie", params=params)
    r.raise_for_status()
    results = r.json().get("results", [])

    brief = []
    for item in results[:max_results]:
        raw_date = item.get("release_date") or ""
        year_str = raw_date[:4] if raw_date else "Unknown"
        poster   = item.get("poster_path")
        brief.append({
            "tmdb_id":      item["id"],
            "title":        item.get("title", "Unknown"),
            "release_year": year_str,
            "overview":     item.get("overview", ""),
            "poster_url":   (TMDB_IMAGE_BASE + poster) if poster else None,
        })
    return brief


# ── FULL METADATA (for DB storage) ───────────────────────────────────────────

def get_full_movie_by_id(tmdb_id):
    """Fetch complete movie metadata by TMDB ID (credits, images, keywords, etc.)."""
    url    = f"{BASE_URL}/movie/{tmdb_id}"
    params = {"api_key": API_KEY, "append_to_response": APPEND}
    r = requests.get(url, params=params)
    r.raise_for_status()
    return r.json()


def get_full_movie_by_name(title):
    """
    Search by title and fetch full metadata for the first match.
    NOTE: Assumes the first result is correct — use search_movies_brief()
          if you need the user to confirm the match first.
    """
    params = {"api_key": API_KEY, "query": title}
    r = requests.get(f"{BASE_URL}/search/movie", params=params)
    r.raise_for_status()
    results = r.json().get("results", [])
    if not results:
        return None
    return get_full_movie_by_id(results[0]["id"])


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TMDB API lookup")
    group  = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--tmdb_id",     help="Lookup movie by TMDB ID")
    group.add_argument("--movie_title", help="Lookup movie by title")
    args = parser.parse_args()

    if args.tmdb_id:
        result = get_full_movie_by_id(args.tmdb_id)
    else:
        result = get_full_movie_by_name(args.movie_title)

    if result:
        print(f"Found: {result['title']} ({result['release_date'][:4]}) — TMDB ID: {result['id']}")
        print(json.dumps(result, indent=2))
    else:
        print("No results found.")