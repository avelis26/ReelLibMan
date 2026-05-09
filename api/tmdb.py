import os
import requests
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

def search_movie(title):
    url = f"{BASE_URL}/search/movie"
    params = {"api_key": API_KEY, "query": title}
    r = requests.get(url, params=params)
    r.raise_for_status()
    results = r.json().get("results", [])
    return results[0] if results else None

if __name__ == "__main__":
    import sys
    query = sys.argv[1] if len(sys.argv) > 1 else "3 Ninjas"
    result = search_movie(query)
    if result:
        print(f"Found: {result['title']} ({result['release_date'][:4]}) — TMDB ID: {result['id']}")
    else:
        print("No results found.")