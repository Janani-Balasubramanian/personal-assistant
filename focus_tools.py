"""
Focus & Pomodoro Productivity Tools for Jarvis.
Tracks deep-work sessions, counts completed pomodoros, provides audio/visual alerts,
and logs focus metrics to the SQLite database.
"""

import datetime as dt
import sqlite3
import threading
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "jarvis.db"

# Global active focus session state
_active_session = {
    "thread": None,
    "stop_event": None,
    "goal": "",
    "start_time": None,
    "duration_minutes": 0,
    "session_id": None,
}
_lock = threading.Lock()


def _init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS focus_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            goal TEXT NOT NULL,
            duration_minutes INTEGER NOT NULL,
            started_at TEXT NOT NULL,
            completed INTEGER NOT NULL DEFAULT 0
        );
        """
    )
    conn.commit()
    conn.close()


_init_db()


def _focus_worker(duration_seconds: int, goal: str, session_id: int, stop_event: threading.Event):
    """Background countdown worker for focus timer."""
    # Sleep in small slices to respond promptly if cancelled
    elapsed = 0
    while elapsed < duration_seconds:
        if stop_event.is_set():
            return
        time.sleep(1)
        elapsed += 1

    # Mark completed in DB
    try:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.execute("UPDATE focus_sessions SET completed = 1 WHERE id = ?", (session_id,))
        conn.commit()
        conn.close()
    except Exception:
        pass

    # Desktop notification
    try:
        from plyer import notification
        notification.notify(
            title="Focus Session Complete!",
            message=f"Outstanding work on: '{goal}'. Time to step back and take a 5-minute break!",
            app_name="Jarvis Focus",
            timeout=12,
        )
    except Exception:
        pass

    # Audio chime & voice alert
    try:
        import winsound
        winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS | winsound.SND_ASYNC)
    except Exception:
        pass

    try:
        import voice
        voice.speak(f"Focus session complete. Fantastic work on {goal}. Time to take a short break.")
    except Exception:
        pass

    with _lock:
        _active_session["thread"] = None
        _active_session["stop_event"] = None


def start_focus_session(duration_minutes: int = 25, goal: str = "Deep Focus Work") -> str:
    """Start a timed focus/pomodoro session with automatic notifications upon completion."""
    global _active_session
    with _lock:
        if _active_session["thread"] and _active_session["thread"].is_alive():
            elapsed = int((time.time() - _active_session["start_time"]) / 60)
            remaining = max(1, _active_session["duration_minutes"] - elapsed)
            return (
                f"A focus session is already in progress: '{_active_session['goal']}'. "
                f"{remaining} minute(s) remaining. Stop it first if you wish to start a new one."
            )

        if duration_minutes <= 0 or duration_minutes > 180:
            return "Please choose a focus duration between 1 and 180 minutes."

        now_iso = dt.datetime.now().isoformat(timespec="seconds")
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        cur = conn.execute(
            "INSERT INTO focus_sessions (goal, duration_minutes, started_at, completed) VALUES (?, ?, ?, 0)",
            (goal.strip(), duration_minutes, now_iso),
        )
        session_id = cur.lastrowid
        conn.commit()
        conn.close()

        stop_event = threading.Event()
        t = threading.Thread(
            target=_focus_worker,
            args=(duration_minutes * 60, goal.strip(), session_id, stop_event),
            daemon=True,
        )
        _active_session["thread"] = t
        _active_session["stop_event"] = stop_event
        _active_session["goal"] = goal.strip()
        _active_session["start_time"] = time.time()
        _active_session["duration_minutes"] = duration_minutes
        _active_session["session_id"] = session_id
        t.start()

    return (
        f"[Focus Session] Started for {duration_minutes} minutes.\n"
        f"Goal: '{goal}'. Muting distractions. I will notify you when it's time to take a break."
    )


def stop_focus_session() -> str:
    """Cancel or stop the currently running focus session."""
    global _active_session
    with _lock:
        if not _active_session["thread"] or not _active_session["thread"].is_alive():
            return "No active focus session is currently running."

        if _active_session["stop_event"]:
            _active_session["stop_event"].set()

        goal = _active_session["goal"]
        _active_session["thread"] = None
        _active_session["stop_event"] = None

    return f"Focus session for '{goal}' has been stopped."


def get_focus_stats() -> str:
    """Retrieve personal focus metrics, completed pomodoro count, and total focus time."""
    today_prefix = dt.date.today().isoformat()
    try:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row

        # All time
        row_total = conn.execute(
            "SELECT COUNT(*) as count, COALESCE(SUM(duration_minutes), 0) as total_min FROM focus_sessions WHERE completed = 1"
        ).fetchone()

        # Today
        row_today = conn.execute(
            "SELECT COUNT(*) as count, COALESCE(SUM(duration_minutes), 0) as total_min FROM focus_sessions WHERE completed = 1 AND started_at LIKE ?",
            (f"{today_prefix}%",),
        ).fetchone()

        # Recent goals
        recent = conn.execute(
            "SELECT goal, duration_minutes, started_at FROM focus_sessions WHERE completed = 1 ORDER BY id DESC LIMIT 3"
        ).fetchall()
        conn.close()

        today_count = row_today["count"]
        today_mins = row_today["total_min"]
        total_count = row_total["count"]
        total_mins = row_total["total_min"]

        lines = [
            "Personal Focus & Productivity Stats:",
            f"- Today: {today_count} completed session(s) ({today_mins} minutes focused)",
            f"- All-Time Total: {total_count} sessions ({total_mins / 60:.1f} hours of deep work)",
        ]

        with _lock:
            if _active_session["thread"] and _active_session["thread"].is_alive():
                elapsed = int((time.time() - _active_session["start_time"]) / 60)
                rem = max(1, _active_session["duration_minutes"] - elapsed)
                lines.append(f"- Active Session: '{_active_session['goal']}' ({rem}m remaining)")

        if recent:
            lines.append("- Recent achievements:")
            for r in recent:
                lines.append(f"   * {r['goal']} ({r['duration_minutes']} min)")

        return "\n".join(lines)
    except Exception as e:
        return f"Unable to fetch focus stats: {e}"


REGISTRY = {
    "start_focus_session": (start_focus_session, False),
    "stop_focus_session": (stop_focus_session, False),
    "get_focus_stats": (get_focus_stats, False),
}

SCHEMAS = [
    {
        "name": "start_focus_session",
        "description": "Start a pomodoro/deep work focus session for a given number of minutes with a specific goal. Jarvis will notify you when complete.",
        "input_schema": {
            "type": "object",
            "properties": {
                "duration_minutes": {
                    "type": "integer",
                    "description": "Length of focus session in minutes (e.g. 25, 45, 60). Defaults to 25.",
                },
                "goal": {
                    "type": "string",
                    "description": "Short description of the work or task being focused on.",
                },
            },
        },
    },
    {
        "name": "stop_focus_session",
        "description": "Cancel or prematurely stop the currently active focus session.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_focus_stats",
        "description": "Get productivity analytics: total focus sessions completed today and all-time, total focused hours, and recent focus milestones.",
        "input_schema": {"type": "object", "properties": {}},
    },
]
