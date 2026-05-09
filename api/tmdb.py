import os
import requests
import argparse
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("TMDB_API_KEY")
BASE_URL = "https://api.themoviedb.org/3"

def get_movie_by_id(tmdb_id):
    url = f"{BASE_URL}/movie/{tmdb_id}"
    params = {"api_key": API_KEY}
    r = requests.get(url, params=params)
    r.raise_for_status()
    return r.json()

def get_movie_by_name(title):
    url = f"{BASE_URL}/search/movie"
    params = {"api_key": API_KEY, "query": title}
    r = requests.get(url, params=params)
    r.raise_for_status()
    results = r.json().get("results", [])
    return results[0] if results else None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TMDB API lookup")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--tmdb_id", help="Lookup movie by TMDB ID")
    group.add_argument("--movie_title", help="Lookup movie by title")
    args = parser.parse_args()

    if args.tmdb_id:
        result = get_movie_by_id(args.tmdb_id)
        print(f"Found: {result['title']} ({result['release_date'][:4]}) — TMDB ID: {result['id']}")
    else:
        result = get_movie_by_name(args.movie_title)
        if result:
            print(f"Found: {result['title']} ({result['release_date'][:4]}) — TMDB ID: {result['id']}")
        else:
            print("No results found.")