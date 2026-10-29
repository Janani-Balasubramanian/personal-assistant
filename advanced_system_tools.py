"""
Advanced system control tools for Jarvis.
Provides deep hardware monitoring, process management, keyboard/mouse automation,
clipboard access, media keys control, and workstation locking.
"""

import os
import subprocess
import sys
import psutil
import pyperclip


def get_system_status() -> str:
    """Get current hardware status: CPU, RAM, Disk, and Battery."""
    cpu_percent = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("C:\\")
    battery = psutil.sensors_battery()

    lines = [
        "System Hardware Status:",
        f"- CPU Usage: {cpu_percent}%",
        f"- RAM: {mem.percent}% used ({mem.used // (1024**2)} MB / {mem.total // (1024**2)} MB)",
        f"- Disk (C:): {disk.percent}% used ({disk.free // (1024**3)} GB free of {disk.total // (1024**3)} GB)",
    ]

    if battery:
        status = "Charging / Plugged in" if battery.power_plugged else "On Battery"
        lines.append(f"- Battery: {battery.percent}% ({status})")
    else:
        lines.append("- Battery: Desktop PC (A/C Power)")

    return "\n".join(lines)


def list_running_apps(limit: int = 10) -> str:
    """List the top running processes consuming memory."""
    procs = []
    for p in psutil.process_iter(["pid", "name", "memory_percent", "cpu_percent"]):
        try:
            info = p.info
            if info["memory_percent"] and info["memory_percent"] > 0.1:
                procs.append(info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    procs.sort(key=lambda x: x["memory_percent"] or 0, reverse=True)
    lines = ["Top active applications & processes:"]
    for p in procs[:limit]:
        mem_pct = p["memory_percent"] or 0
        lines.append(f"- {p['name']} (PID {p['pid']}): RAM {mem_pct:.1f}%")
    return "\n".join(lines)


def close_app(process_name: str) -> str:
    """Close or terminate a process by name (e.g. 'chrome.exe', 'notepad.exe')."""
    if not process_name.lower().endswith(".exe") and sys.platform == "win32":
        process_name += ".exe"

    killed = 0
    for p in psutil.process_iter(["pid", "name"]):
        try:
            if p.info["name"].lower() == process_name.lower():
                p.terminate()
                killed += 1
        except Exception:
            pass

    if killed > 0:
        return f"Terminated {killed} instance(s) of '{process_name}'."
    return f"No running process found with name '{process_name}'."


def press_hotkey(keys: str) -> str:
    """
    Press a keyboard shortcut combo on the user's system.
    Examples: 'win+d' (minimize/show desktop), 'alt+tab', 'ctrl+shift+esc' (task manager),
    'ctrl+c', 'ctrl+v', 'f11', 'win+e' (file explorer).
    """
    try:
        import pyautogui
        parts = [k.strip().lower() for k in keys.split("+")]
        pyautogui.hotkey(*parts)
        return f"Pressed shortcut '{keys}'."
    except Exception as e:
        return f"Failed to press hotkey: {e}"


def type_text(text: str) -> str:
    """Type text into the currently active window on screen."""
    try:
        import pyautogui
        pyautogui.write(text, interval=0.02)
        return f"Typed: '{text[:80]}'..."
    except Exception as e:
        return f"Failed to type text: {e}"


def read_clipboard() -> str:
    """Read the current text content from the Windows clipboard."""
    import time
    for _ in range(3):
        try:
            content = pyperclip.paste()
            if not content:
                return "Clipboard is currently empty."
            return f"Clipboard content:\n{content[:2000]}"
        except Exception:
            time.sleep(0.08)
    return "Clipboard is currently empty or locked by another application."


def write_clipboard(text: str) -> str:
    """Copy text into the Windows clipboard."""
    import time
    for _ in range(3):
        try:
            pyperclip.copy(text)
            return f"Copied to clipboard: '{text[:80]}...'"
        except Exception:
            time.sleep(0.08)
    return "Failed to access clipboard."


def media_control(action: str) -> str:
    """
    Control system media playback.
    Action can be: 'play_pause', 'next', 'prev', 'mute'.
    """
    try:
        import win32api
        import win32con

        action = action.lower().strip()
        key_map = {
            "play_pause": win32con.VK_MEDIA_PLAY_PAUSE,
            "play": win32con.VK_MEDIA_PLAY_PAUSE,
            "pause": win32con.VK_MEDIA_PLAY_PAUSE,
            "next": win32con.VK_MEDIA_NEXT_TRACK,
            "next_track": win32con.VK_MEDIA_NEXT_TRACK,
            "prev": win32con.VK_MEDIA_PREV_TRACK,
            "prev_track": win32con.VK_MEDIA_PREV_TRACK,
            "mute": win32con.VK_VOLUME_MUTE,
        }

        if action not in key_map:
            return f"Unknown media action '{action}'. Options: play_pause, next, prev, mute."

        vk = key_map[action]
        win32api.keybd_event(vk, 0, 0, 0)
        win32api.keybd_event(vk, 0, win32con.KEYEVENTF_KEYUP, 0)
        return f"Media action '{action}' triggered."
    except Exception as e:
        return f"Media control failed: {e}"


def lock_workstation() -> str:
    """Lock the Windows workstation immediately."""
    try:
        if sys.platform == "win32":
            subprocess.run("rundll32.exe user32.dll,LockWorkStation", shell=True)
            return "Workstation locked successfully."
        return "Workstation locking is only supported on Windows."
    except Exception as e:
        return f"Failed to lock workstation: {e}"


REGISTRY = {
    "get_system_status": (get_system_status, False),
    "list_running_apps": (list_running_apps, False),
    "close_app": (close_app, True),
    "press_hotkey": (press_hotkey, False),
    "type_text": (type_text, False),
    "read_clipboard": (read_clipboard, False),
    "write_clipboard": (write_clipboard, False),
    "media_control": (media_control, False),
    "lock_workstation": (lock_workstation, False),
}

SCHEMAS = [
    {
        "name": "get_system_status",
        "description": "Get current hardware statistics: CPU load %, RAM usage, free Disk space, and Battery level.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "list_running_apps",
        "description": "List top running applications and processes on the system sorted by memory usage.",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Number of processes to list (default 10)"}
            },
        },
    },
    {
        "name": "close_app",
        "description": "Gracefully close or terminate a process/app by name (e.g. 'chrome.exe', 'notepad.exe'). Requires user confirmation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "process_name": {"type": "string", "description": "Process name, e.g. 'notepad.exe' or 'calc.exe'"}
            },
            "required": ["process_name"],
        },
    },
    {
        "name": "press_hotkey",
        "description": "Press a keyboard shortcut combo on the system, such as 'win+d' (minimize/show desktop), 'alt+tab', 'ctrl+shift+esc', 'ctrl+c', 'ctrl+v', 'win+e'.",
        "input_schema": {
            "type": "object",
            "properties": {
                "keys": {"type": "string", "description": "Hotkey string, e.g. 'win+d'"}
            },
            "required": ["keys"],
        },
    },
    {
        "name": "type_text",
        "description": "Type text into the currently focused window on screen as if typed from keyboard.",
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "The text to type"}
            },
            "required": ["text"],
        },
    },
    {
        "name": "read_clipboard",
        "description": "Read the current text from the user's Windows clipboard.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "write_clipboard",
        "description": "Copy text into the user's Windows clipboard.",
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to copy"}
            },
            "required": ["text"],
        },
    },
    {
        "name": "media_control",
        "description": "Control audio/video media playback: 'play_pause', 'next', 'prev', 'mute'.",
        "input_schema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Action: 'play_pause', 'next', 'prev', or 'mute'",
                    "enum": ["play_pause", "next", "prev", "mute"]
                }
            },
            "required": ["action"],
        },
    },
    {
        "name": "lock_workstation",
        "description": "Immediately lock the Windows computer screen for security.",
        "input_schema": {"type": "object", "properties": {}},
    },
]
