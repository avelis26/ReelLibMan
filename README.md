# Reel Library Manager Project Blueprint (WIP)

> A cross-platform media library manager with an emphasis on user-friendly operation.
> Philosophy: Lean, fast, offline-capable, user-controlled. Linux first, Windows supported.

---

## 0. Dev Set Up

```fish
sudo pacman -S python-dotenv python-requests
```

## 1. Goals

- Organize media library files at the folder/file level based on configurable structure templates
- Rename files and folders to match configurable naming conventions
- Fetch and cache metadata from online sources (TMDB, TVDB)
- Produce a media library fully compatible with Emby / Jellyfin / Plex
- Never require the internet after initial metadata fetch and cache
- Remain lean — no bloat, no unnecessary features
- Completely self contained install / setup with dependacies

---

## 2. Out of Scope Goals

- CLI operations you could access via SSH for remote library management
- WebUI (possibly with remote access) which would be just the normal GUI in the browser

---

## 3. Tech Stack

| Layer | Choice | Reason |
|---|---|---|
| Language | Python 3.12+ | Ecosystem, speed of development, readability |
| GUI Framework | PyQt6 | Modern, cross-platform, Electron-like polish |
| Local Database | SQLite (via SQLAlchemy) | Fast, self-contained, no server required |
| Packaging (Linux) | AppImage | Self-contained, no system dependencies |
| Packaging (Windows) | PyInstaller | Single executable |
| API: Movies | TMDB (themoviedb.org) | Free, well-documented, no rate limit issues |
| API: TV Shows | TVDB (thetvdb.com) | Free for personal/low-revenue use |

---

## 4. Project Structure (Proposed)

```
ReelLibMan/
├── main.py                             # Entry point
├── config/
│   └── settings.py                     # User config loader/saver
├── core/
│   ├── scanner.py                      # File system scanner
│   ├── matcher.py                      # Match files to metadata
│   ├── renamer.py                      # Rename/move files per convention
│   └── organizer.py                    # Folder structure enforcement
├── api/
│   ├── get_movie_tmdb_api_data.py      # TMDB API client
│   └── tvdb.py                         # TVDB API client
├── cache/
│   └── db.py                           # SQLite cache layer (SQLAlchemy)
├── gui/
│   ├── main_window.py                  # Main application window
│   ├── movie_view.py                   # Movie library view
│   └── settings_view.py                # Settings / config UI
├── models/
│   ├── movie.py                        # Movie data model
│   └── show.py                         # TV show data model (Phase 2)
├── utils/
│   └── helpers.py                      # Shared utility functions
├── tests/
│   └── ...                             # Unit tests
├── BLUEPRINT.md
├── README.md
```

---

## 5. Core Features — Phase 1 (Movies)

### 5.1 Library Scanning
- User defines one or more root library paths in settings
- Scanner recursively walks paths and identifies media files by extension
- Supported extensions: `.mkv`, `.mp4`, `.avi`, `.m4v`, `.mov` (configurable)

### 5.2 Metadata Fetching
- Match identified files to TMDB records by filename parsing
- Fetch: title, year, overview, genres, poster, backdrop, rating, cast
- All fetched data stored in local SQLite cache
- Never re-fetch if cache record exists (manual refresh override available)

### 5.3 File Naming Convention
- User defines naming template in settings
- Default template: `{title} ({year})`
- Tokens available: `{title}`, `{year}`, `{tmdb_id}`, `{rating}`, `{genre}`
- ReelLibMan renames files and folders to match template on user confirmation

### 5.4 Folder Organization
- User defines folder structure template in settings
- Default template: `{root}/{title} ({year})/`
- ReelLibMan moves files into correct structure on user confirmation
- Never destructive without explicit user approval (dry-run preview first)

### 5.5 Emby / Jellyfin Compatibility
- Output NFO metadata sidecar files per Emby/Jellyfin spec
- Download and store poster/backdrop images alongside media files
- Library is fully functional offline after initial metadata fetch

### 5.6 Settings
- Library root paths (multiple supported)
- File naming template
- Folder structure template
- Supported file extensions
- TMDB API key
- TVDB API key / subscription PIN
- Dry-run mode toggle (preview changes without applying)

---

## 6. Core Features — Phase 2 (TV Shows)

- TVDB integration for series, season, and episode metadata
- TV-specific naming convention tokens: `{series}`, `{season}`, `{episode}`, `{episode_title}`
- Default TV template: `{series}/Season {season}/{series} - S{season}E{episode} - {episode_title}`
- NFO sidecar files per Emby/Jellyfin TV spec
- Multi-episode file handling

---

## 7. Core Features — Phase 3 (Polish / Go-to-Market)

- Duplicate detection
- Batch operations with progress UI
- One-click AppImage / installer build pipeline
- Auto-update mechanism
- TMDB commercial license compliance review
- TVDB license tier review based on revenue
- Attribution UI (required by both APIs)

---

## 8. Data Flow

```
User adds library path
        ↓
Scanner identifies media files
        ↓
Matcher parses filenames → queries TMDB/TVDB (if not cached)
        ↓
Results stored in SQLite cache
        ↓
User reviews matches in GUI
        ↓
User confirms → Renamer + Organizer apply changes
        ↓
NFO + images written alongside media files
        ↓
Library ready for Emby / Jellyfin (online or air-gapped)
```

---

## 9. Design Principles

- **Cache first** — hit the API once, never again unless forced
- **Never destructive** — always dry-run preview before any file operation
- **Config driven** — naming and structure are templates, never hardcoded
- **Offline capable** — after initial fetch, zero internet dependency
- **Lean** — if a feature isn't in this document, it doesn't get built (yet)

---

## 10. Open Questions / Future Decisions

- [ ] How to handle multi-version files (e.g. theatrical vs extended cut)?
- [ ] Manual match override UI when auto-match confidence is low?
- [ ] Support for subtitle files (.srt, .ass) during rename/move operations?
- [ ] Trailer/extras handling?
- [ ] Windows packaging strategy (PyInstaller vs NSIS installer)?

---

*This is a living document. Update before coding, not after.*
Non-Goals (explicitly o