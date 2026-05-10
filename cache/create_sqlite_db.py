"""
ReelLibMan database creation script.

Creates the SQLite database and schema from scratch.
WARNING: Running this will drop and recreate all tables (nuke and pave).

Usage:
    python cache/create_db.py
"""

import os
import sqlite3
from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.path.expanduser(os.getenv("SQLITE_DB"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS movies (
    tmdb_id             INTEGER PRIMARY KEY,
    imdb_id             TEXT,
    title               TEXT NOT NULL,
    original_title      TEXT,
    tagline             TEXT,
    overview            TEXT,
    runtime             INTEGER,
    release_date        TEXT,
    status              TEXT,
    original_language   TEXT,
    budget              INTEGER,
    revenue             INTEGER,
    popularity          REAL,
    vote_average        REAL,
    vote_count          INTEGER,
    adult               INTEGER DEFAULT 0,
    poster_path         TEXT,
    backdrop_path       TEXT,
    collection_id       INTEGER,
    collection_name     TEXT,
    certification       TEXT,
    fetched_at          TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS genres (
    id      INTEGER PRIMARY KEY,
    name    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS movie_genres (
    tmdb_id     INTEGER REFERENCES movies(tmdb_id),
    genre_id    INTEGER REFERENCES genres(id),
    PRIMARY KEY (tmdb_id, genre_id)
);

CREATE TABLE IF NOT EXISTS keywords (
    id      INTEGER PRIMARY KEY,
    name    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS movie_keywords (
    tmdb_id     INTEGER REFERENCES movies(tmdb_id),
    keyword_id  INTEGER REFERENCES keywords(id),
    PRIMARY KEY (tmdb_id, keyword_id)
);

CREATE TABLE IF NOT EXISTS companies (
    id              INTEGER PRIMARY KEY,
    name            TEXT NOT NULL,
    origin_country  TEXT,
    logo_path       TEXT
);

CREATE TABLE IF NOT EXISTS movie_companies (
    tmdb_id     INTEGER REFERENCES movies(tmdb_id),
    company_id  INTEGER REFERENCES companies(id),
    PRIMARY KEY (tmdb_id, company_id)
);

CREATE TABLE IF NOT EXISTS movie_countries (
    tmdb_id         INTEGER REFERENCES movies(tmdb_id),
    iso_3166_1      TEXT,
    name            TEXT,
    PRIMARY KEY (tmdb_id, iso_3166_1)
);

CREATE TABLE IF NOT EXISTS movie_languages (
    tmdb_id         INTEGER REFERENCES movies(tmdb_id),
    iso_639_1       TEXT,
    name            TEXT,
    PRIMARY KEY (tmdb_id, iso_639_1)
);

CREATE TABLE IF NOT EXISTS people (
    id              INTEGER PRIMARY KEY,
    name            TEXT NOT NULL,
    original_name   TEXT,
    profile_path    TEXT,
    known_for       TEXT
);

CREATE TABLE IF NOT EXISTS movie_cast (
    tmdb_id     INTEGER REFERENCES movies(tmdb_id),
    person_id   INTEGER REFERENCES people(id),
    character   TEXT,
    cast_order  INTEGER,
    credit_id   TEXT,
    PRIMARY KEY (tmdb_id, credit_id)
);

CREATE TABLE IF NOT EXISTS movie_crew (
    tmdb_id     INTEGER REFERENCES movies(tmdb_id),
    person_id   INTEGER REFERENCES people(id),
    department  TEXT,
    job         TEXT,
    credit_id   TEXT,
    PRIMARY KEY (tmdb_id, credit_id)
);

CREATE TABLE IF NOT EXISTS movie_images (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    tmdb_id     INTEGER REFERENCES movies(tmdb_id),
    image_type  TEXT NOT NULL,
    file_path   TEXT NOT NULL,
    width       INTEGER,
    height      INTEGER,
    iso_639_1   TEXT,
    vote_average REAL,
    vote_count  INTEGER
);

CREATE TABLE IF NOT EXISTS movie_release_dates (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    tmdb_id         INTEGER REFERENCES movies(tmdb_id),
    iso_3166_1      TEXT,
    certification   TEXT,
    release_date    TEXT,
    release_type    INTEGER
);
"""

def nuke_and_pave():
    """Drop all tables and recreate the schema from scratch."""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"Existing database removed: {DB_PATH}")

    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()
    print(f"Database created: {DB_PATH}")

if __name__ == "__main__":
    nuke_and_pave()