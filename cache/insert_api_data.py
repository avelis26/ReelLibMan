"""
ReelLibMan database insert script.

Inserts or replaces TMDB API movie data into the SQLite database.
Called by main.py after a successful API fetch.

Usage:
    Not called directly — imported and called by main.py.
"""

import os
import sqlite3
from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.path.expanduser(os.getenv("SQLITE_DB"))


def get_connection():
    """Return a connection to the SQLite database."""
    return sqlite3.connect(DB_PATH)


def save_movie(data: dict):
    """
    Insert or replace all movie data from a TMDB API response into the database.

    Args:
        data (dict): Full TMDB API response including appended credits,
                     release_dates, keywords, images, and external_ids.
    """
    conn = get_connection()
    try:
        _insert_movie(conn, data)
        _insert_genres(conn, data)
        _insert_keywords(conn, data)
        _insert_companies(conn, data)
        _insert_countries(conn, data)
        _insert_languages(conn, data)
        _insert_people_and_cast(conn, data)
        _insert_people_and_crew(conn, data)
        _insert_images(conn, data)
        _insert_release_dates(conn, data)
        conn.commit()
        print(f"Saved: {data['title']} ({data.get('release_date', '')[:4]}) — TMDB ID: {data['id']}")
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def _get_us_certification(data: dict) -> str:
    """Extract US theatrical certification from release_dates."""
    for entry in data.get("release_dates", {}).get("results", []):
        if entry["iso_3166_1"] == "US":
            for rd in entry["release_dates"]:
                if rd["type"] == 3 and rd.get("certification"):
                    return rd["certification"]
    return ""


def _insert_movie(conn, data):
    collection = data.get("belongs_to_collection") or {}
    conn.execute("""
        INSERT OR REPLACE INTO movies (
            tmdb_id, imdb_id, title, original_title, tagline, overview,
            runtime, release_date, status, original_language, budget, revenue,
            popularity, vote_average, vote_count, adult, poster_path,
            backdrop_path, collection_id, collection_name, certification
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["id"],
        data.get("imdb_id") or data.get("external_ids", {}).get("imdb_id"),
        data["title"],
        data.get("original_title"),
        data.get("tagline"),
        data.get("overview"),
        data.get("runtime"),
        data.get("release_date"),
        data.get("status"),
        data.get("original_language"),
        data.get("budget"),
        data.get("revenue"),
        data.get("popularity"),
        data.get("vote_average"),
        data.get("vote_count"),
        int(data.get("adult", False)),
        data.get("poster_path"),
        data.get("backdrop_path"),
        collection.get("id"),
        collection.get("name"),
        _get_us_certification(data)
    ))


def _insert_genres(conn, data):
    for g in data.get("genres", []):
        conn.execute("INSERT OR IGNORE INTO genres (id, name) VALUES (?, ?)", (g["id"], g["name"]))
        conn.execute("INSERT OR IGNORE INTO movie_genres (tmdb_id, genre_id) VALUES (?, ?)", (data["id"], g["id"]))


def _insert_keywords(conn, data):
    for k in data.get("keywords", {}).get("keywords", []):
        conn.execute("INSERT OR IGNORE INTO keywords (id, name) VALUES (?, ?)", (k["id"], k["name"]))
        conn.execute("INSERT OR IGNORE INTO movie_keywords (tmdb_id, keyword_id) VALUES (?, ?)", (data["id"], k["id"]))


def _insert_companies(conn, data):
    for c in data.get("production_companies", []):
        conn.execute("""
            INSERT OR IGNORE INTO companies (id, name, origin_country, logo_path)
            VALUES (?, ?, ?, ?)
        """, (c["id"], c["name"], c.get("origin_country"), c.get("logo_path")))
        conn.execute("INSERT OR IGNORE INTO movie_companies (tmdb_id, company_id) VALUES (?, ?)", (data["id"], c["id"]))


def _insert_countries(conn, data):
    for c in data.get("production_countries", []):
        conn.execute("INSERT OR IGNORE INTO movie_countries (tmdb_id, iso_3166_1, name) VALUES (?, ?, ?)",
                     (data["id"], c["iso_3166_1"], c["name"]))


def _insert_languages(conn, data):
    for l in data.get("spoken_languages", []):
        conn.execute("INSERT OR IGNORE INTO movie_languages (tmdb_id, iso_639_1, name) VALUES (?, ?, ?)",
                     (data["id"], l["iso_639_1"], l.get("english_name") or l.get("name")))


def _insert_people_and_cast(conn, data):
    for p in data.get("credits", {}).get("cast", []):
        conn.execute("""
            INSERT OR IGNORE INTO people (id, name, original_name, profile_path, known_for)
            VALUES (?, ?, ?, ?, ?)
        """, (p["id"], p["name"], p.get("original_name"), p.get("profile_path"), p.get("known_for_department")))
        conn.execute("""
            INSERT OR IGNORE INTO movie_cast (tmdb_id, person_id, character, cast_order, credit_id)
            VALUES (?, ?, ?, ?, ?)
        """, (data["id"], p["id"], p.get("character"), p.get("order"), p["credit_id"]))


def _insert_people_and_crew(conn, data):
    for p in data.get("credits", {}).get("crew", []):
        conn.execute("""
            INSERT OR IGNORE INTO people (id, name, original_name, profile_path, known_for)
            VALUES (?, ?, ?, ?, ?)
        """, (p["id"], p["name"], p.get("original_name"), p.get("profile_path"), p.get("known_for_department")))
        conn.execute("""
            INSERT OR IGNORE INTO movie_crew (tmdb_id, person_id, department, job, credit_id)
            VALUES (?, ?, ?, ?, ?)
        """, (data["id"], p["id"], p.get("department"), p.get("job"), p["credit_id"]))


def _insert_images(conn, data):
    conn.execute("DELETE FROM movie_images WHERE tmdb_id = ?", (data["id"],))
    images = data.get("images", {})
    for img_type, items in [("poster", images.get("posters", [])),
                             ("backdrop", images.get("backdrops", [])),
                             ("logo", images.get("logos", []))]:
        for img in items:
            conn.execute("""
                INSERT INTO movie_images (tmdb_id, image_type, file_path, width, height, iso_639_1, vote_average, vote_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (data["id"], img_type, img["file_path"], img.get("width"), img.get("height"),
                  img.get("iso_639_1"), img.get("vote_average"), img.get("vote_count")))


def _insert_release_dates(conn, data):
    conn.execute("DELETE FROM movie_release_dates WHERE tmdb_id = ?", (data["id"],))
    for entry in data.get("release_dates", {}).get("results", []):
        for rd in entry.get("release_dates", []):
            conn.execute("""
                INSERT INTO movie_release_dates (tmdb_id, iso_3166_1, certification, release_date, release_type)
                VALUES (?, ?, ?, ?, ?)
            """, (data["id"], entry["iso_3166_1"], rd.get("certification"), rd.get("release_date"), rd.get("type")))