"""
Desktop & Local File Navigation Tools for Jarvis.
Quickly search local files across Desktop, Downloads, and Documents, inspect recent downloads,
and open files or folders in Windows Explorer.
"""

import datetime as dt
import os
import sys
from pathlib import Path

USER_HOME = Path.home()
DIRECTORIES = {
    "desktop": USER_HOME / "Desktop",
    "downloads": USER_HOME / "Downloads",
    "documents": USER_HOME / "Documents",
}


def _format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024**2:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024**2):.1f} MB"


def search_local_files(query: str, location: str = "all", max_results: int = 10) -> str:
    """Search for files matching a keyword or file extension across Desktop, Downloads, and Documents."""
    query = query.strip().lower()
    if not query:
        return "Search query cannot be empty."

    targets = []
    loc = location.lower().strip()
    if loc in DIRECTORIES:
        targets.append((loc, DIRECTORIES[loc]))
    else:
        for name, p in DIRECTORIES.items():
            if p.exists():
                targets.append((name, p))

    matches = []
    for loc_name, folder in targets:
        try:
            # Walk top 2 levels to keep search fast and avoid scanning massive node_modules or deep trees
            for root, dirs, files in os.walk(folder):
                rel_depth = len(Path(root).relative_to(folder).parts)
                if rel_depth > 2:
                    dirs.clear()
                    continue

                # Skip hidden folders like .git, AppData, etc.
                dirs[:] = [d for d in dirs if not d.startswith(".")]

                for f in files:
                    if query in f.lower():
                        full_path = Path(root) / f
                        try:
                            stat = full_path.stat()
                            mtime = dt.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                            matches.append({
                                "name": f,
                                "path": str(full_path),
                                "size": _format_size(stat.st_size),
                                "modified": mtime,
                                "mtime_raw": stat.st_mtime,
                                "location": loc_name,
                            })
                        except Exception:
                            pass
        except Exception:
            continue

    if not matches:
        return f"No files matching '{query}' found in {location}."

    # Sort most recent first
    matches.sort(key=lambda x: x["mtime_raw"], reverse=True)
    matches = matches[:max_results]

    lines = [f"Found {len(matches)} matching file(s):"]
    for i, m in enumerate(matches, 1):
        lines.append(f"{i}. {m['name']} ({m['size']}, {m['modified']})\n   Path: {m['path']}")

    return "\n".join(lines)


def get_recent_downloads(limit: int = 5) -> str:
    """List the most recently downloaded files in the Downloads folder."""
    downloads_dir = DIRECTORIES["downloads"]
    if not downloads_dir.exists():
        return "Downloads folder not found."

    try:
        files = []
        for p in downloads_dir.iterdir():
            if p.is_file() and not p.name.startswith("."):
                try:
                    stat = p.stat()
                    files.append((stat.st_mtime, stat.st_size, p))
                except Exception:
                    continue

        if not files:
            return "No files found in Downloads."

        files.sort(key=lambda x: x[0], reverse=True)
        files = files[:limit]

        lines = [f"Recent Downloads (Top {len(files)}):"]
        for i, (mtime, size, path) in enumerate(files, 1):
            date_str = dt.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
            lines.append(f"{i}. {path.name} ({_format_size(size)}, {date_str})\n   Path: {path}")

        return "\n".join(lines)
    except Exception as e:
        return f"Failed to list downloads: {e}"


def open_file_or_folder(path: str) -> str:
    """Open a file or folder on Windows in the default app or File Explorer."""
    clean_path = path.strip().strip('"').strip("'")
    target = Path(clean_path).expanduser().resolve()

    if not target.exists():
        return f"Path does not exist: {path}"

    try:
        if sys.platform == "win32":
            os.startfile(str(target))
        else:
            import subprocess
            subprocess.Popen(["xdg-open", str(target)])
        return f"Opened: {target}"
    except Exception as e:
        return f"Failed to open '{target}': {e}"


REGISTRY = {
    "search_local_files": (search_local_files, False),
    "get_recent_downloads": (get_recent_downloads, False),
    "open_file_or_folder": (open_file_or_folder, False),
}

SCHEMAS = [
    {
        "name": "search_local_files",
        "description": "Search local files by name or extension on Desktop, Downloads, and Documents.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Filename, keyword, or extension to search (e.g. 'resume', 'report.pdf', '.png')",
                },
                "location": {
                    "type": "string",
                    "enum": ["all", "desktop", "downloads", "documents"],
                    "description": "Where to search. Defaults to 'all'.",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return (default 10).",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_recent_downloads",
        "description": "List the most recently downloaded files in the user's Downloads folder.",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Number of recent files to return (default 5).",
                }
            },
        },
    },
    {
        "name": "open_file_or_folder",
        "description": "Open a local file or directory in Windows File Explorer or its default application.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Full file or folder path to open.",
                }
            },
            "required": ["path"],
        },
    },
]

