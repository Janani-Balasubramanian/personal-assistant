"""
Projects tools for Jarvis.
Allows listing projects, reading project files, inspecting git status, and running tests.
"""

import json
import os
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PROJECTS_CONFIG = Path(os.getenv("JARVIS_PROJECTS_FILE", str(BASE_DIR / "projects.json")))


def _load_projects() -> dict:
    if not PROJECTS_CONFIG.exists():
        return {}
    try:
        return json.loads(PROJECTS_CONFIG.read_text(encoding="utf-8"))
    except Exception:
        return {}


def list_projects() -> str:
    """List all registered coding projects."""
    projects = _load_projects()
    if not projects:
        return "No projects registered in projects.json."
    lines = []
    for key, info in projects.items():
        desc = info.get("description", "")
        path = info.get("path", "")
        lines.append(f"- {key}: {desc} ({path})")
    return "\n".join(lines)


def read_project_file(project: str, path: str) -> str:
    """Read a file within a coding project."""
    projects = _load_projects()
    if project not in projects:
        return f"Unknown project '{project}'. Available: {', '.join(projects.keys())}"
    proj_dir = Path(projects[project]["path"]).resolve()
    target_path = (proj_dir / path).resolve()

    if not str(target_path).startswith(str(proj_dir)):
        return "Access denied: cannot read files outside the project root."
    if not target_path.exists():
        return f"File '{path}' does not exist in project '{project}'."
    if target_path.is_dir():
        entries = [f.name for f in target_path.iterdir()]
        return f"Directory contents:\n" + "\n".join(f"- {e}" for e in sorted(entries)[:50])

    try:
        content = target_path.read_text(encoding="utf-8", errors="replace")
        return content[:4000] + ("\n...[truncated]" if len(content) > 4000 else "")
    except Exception as e:
        return f"Error reading file: {e}"


def check_git_status(project: str) -> str:
    """Check git branch and status of a project."""
    projects = _load_projects()
    if project not in projects:
        return f"Unknown project '{project}'. Available: {', '.join(projects.keys())}"
    proj_dir = Path(projects[project]["path"]).resolve()
    if not proj_dir.exists():
        return f"Project path does not exist: {proj_dir}"

    try:
        proc = subprocess.run(
            ["git", "status", "-s", "-b"],
            cwd=str(proj_dir),
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
        )
        output = (proc.stdout + proc.stderr).strip()
        return output or "Working tree clean."
    except Exception as e:
        return f"Git error: {e}"


def run_tests(project: str) -> str:
    """Run tests for a project (requires user confirmation)."""
    projects = _load_projects()
    if project not in projects:
        return f"Unknown project '{project}'. Available: {', '.join(projects.keys())}"
    info = projects[project]
    proj_dir = Path(info["path"]).resolve()
    cmd = info.get("test_command", "pytest")

    try:
        proc = subprocess.run(
            cmd,
            cwd=str(proj_dir),
            shell=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )
        out = (proc.stdout + proc.stderr).strip()
        status = "PASSED" if proc.returncode == 0 else f"FAILED (exit code {proc.returncode})"
        return f"Tests {status}:\n{out[:2000]}"
    except Exception as e:
        return f"Test runner error: {e}"


REGISTRY = {
    "list_projects": (list_projects, False),
    "read_project_file": (read_project_file, False),
    "check_git_status": (check_git_status, False),
    "run_tests": (run_tests, True),
}

SCHEMAS = [
    {
        "name": "list_projects",
        "description": "List all registered coding projects and their locations.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "read_project_file",
        "description": "Read a source code or document file within a project.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project": {"type": "string", "description": "Project identifier from list_projects"},
                "path": {"type": "string", "description": "Relative file path inside the project"},
            },
            "required": ["project", "path"],
        },
    },
    {
        "name": "check_git_status",
        "description": "Check the git status (current branch, modified files) for a project.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project": {"type": "string", "description": "Project identifier from list_projects"}
            },
            "required": ["project"],
        },
    },
    {
        "name": "run_tests",
        "description": "Run the automated tests for a given project. Requires user approval.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project": {"type": "string", "description": "Project identifier from list_projects"}
            },
            "required": ["project"],
        },
    },
]
