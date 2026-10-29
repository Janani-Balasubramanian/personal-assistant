"""
Notes tools for Jarvis.
Allows reading, searching, listing, and saving study notes in the notes directory.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
NOTES_DIR = Path(os.getenv("JARVIS_NOTES_DIR", str(BASE_DIR / "notes")))
NOTES_DIR.mkdir(parents=True, exist_ok=True)


def list_notes() -> str:
    """List all notes in the study notes directory."""
    if not NOTES_DIR.exists():
        return "No notes directory found."
    files = [f.name for f in NOTES_DIR.iterdir() if f.is_file()]
    if not files:
        return "No notes found in the notes folder."
    return "\n".join(f"- {name}" for name in sorted(files))


def read_note(filename: str) -> str:
    """Read a specific note file by name."""
    path = (NOTES_DIR / filename).resolve()
    # Prevent directory traversal
    if not str(path).startswith(str(NOTES_DIR.resolve())):
        return "Access denied: file is outside notes directory."
    if not path.exists():
        return f"Note '{filename}' does not exist."

    suffix = path.suffix.lower()
    if suffix in {".txt", ".md", ".json", ".csv", ".py"}:
        try:
            return path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            return f"Error reading file: {e}"
    elif suffix == ".pdf":
        try:
            import pypdf
            reader = pypdf.PdfReader(str(path))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
            return text.strip() or "(Empty PDF)"
        except ImportError:
            return "pypdf library not installed. Run 'pip install pypdf' to read PDFs."
        except Exception as e:
            return f"Error reading PDF: {e}"
    elif suffix == ".docx":
        try:
            import docx
            doc = docx.Document(str(path))
            return "\n".join(p.text for p in doc.paragraphs)
        except ImportError:
            return "python-docx library not installed. Run 'pip install python-docx' to read DOCX."
        except Exception as e:
            return f"Error reading DOCX: {e}"
    else:
        try:
            return path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return f"Unsupported file type: {suffix}"


def search_notes(query: str) -> str:
    """Search study notes for a keyword or phrase."""
    if not NOTES_DIR.exists():
        return "No notes directory found."
    query_lower = query.strip().lower()
    matches = []
    for f in sorted(NOTES_DIR.iterdir()):
        if f.is_file():
            content = read_note(f.name)
            if query_lower in f.name.lower() or query_lower in content.lower():
                # Extract snippet
                snippet = ""
                idx = content.lower().find(query_lower)
                if idx != -1:
                    start = max(0, idx - 40)
                    end = min(len(content), idx + 80)
                    snippet = f" ...{content[start:end].replace(chr(10), ' ')}..."
                matches.append(f"{f.name}:{snippet}")

    if not matches:
        return f"No notes matched '{query}'."
    return "\n".join(matches)


def save_note(filename: str, content: str) -> str:
    """Create or overwrite a note in the notes directory."""
    if not filename.endswith((".txt", ".md")):
        filename += ".txt"
    path = (NOTES_DIR / filename).resolve()
    if not str(path).startswith(str(NOTES_DIR.resolve())):
        return "Access denied: invalid file path."
    try:
        path.write_text(content, encoding="utf-8")
        return f"Saved note '{filename}' successfully."
    except Exception as e:
        return f"Failed to save note: {e}"


REGISTRY = {
    "list_notes": (list_notes, False),
    "read_note": (read_note, False),
    "search_notes": (search_notes, False),
    "save_note": (save_note, False),
}

SCHEMAS = [
    {
        "name": "list_notes",
        "description": "List all note and study files available in the notes folder.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "read_note",
        "description": "Read the contents of a note or document by filename.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "Name of the file, e.g. 'history_chapter1.txt'"}
            },
            "required": ["filename"],
        },
    },
    {
        "name": "search_notes",
        "description": "Search across all notes for a specific keyword or topic.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Keyword to look for in notes"}
            },
            "required": ["query"],
        },
    },
    {
        "name": "save_note",
        "description": "Save or update a note in the notes folder.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "Filename, e.g. 'meeting_notes.txt'"},
                "content": {"type": "string", "description": "Content of the note"},
            },
            "required": ["filename", "content"],
        },
    },
]
