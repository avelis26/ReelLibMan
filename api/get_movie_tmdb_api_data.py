"""
TMDB API client for ReelLibMan.

Provides functions to fetch full movie metadata from the TMDB API
including credits, images, keywords, and external IDs.

Usage:
    python tmdb.py --tmdb_id 16314
    python tmdb.py --movie_title "3 Ninjas"
"""

import os
import json
import requests
import argparse
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("TMDB_API_KEY")
BASE_URL = "https://api.themoviedb.org/3"
APPEND = "credits,release_dates,keywords,images,external_ids"

def get_movie_by_id(tmdb_id):
    url = f"{BASE_URL}/movie/{tmdb_id}"
    params = {"api_key": API_KEY, "append_to_response": APPEND}
    r = requests.get(url, params=params)
    r.raise_for_status()
    return r.json()

def get_movie_by_name(title):
    url = f"{BASE_URL}/search/movie"
    params = {"api_key": API_KEY, "query": title}
    r = requests.get(url, params=params)
    r.raise_for_status()
    results = r.json().get("results", [])
    if not results:
        return None
    # Got a match, now fetch full data using the TMDB ID
    return get_movie_by_id(results[0]["id"])

def print_results(result):
    print(f"Found: {result['title']} ({result['release_date'][:4]}) — TMDB ID: {result['id']}")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TMDB API lookup")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--tmdb_id", help="Lookup movie by TMDB ID")
    group.add_argument("--movie_title", help="Lookup movie by title")
    args = parser.parse_args()

    if args.tmdb_id:
        result = get_movie_by_id(args.tmdb_id)
        print_results(result)
    elif args.movie_title:
        result = get_movie_by_name(args.movie_title)
        if result:
            print_results(result)
        else:
            print("No results found.")