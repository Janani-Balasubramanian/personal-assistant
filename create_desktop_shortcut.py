"""
Creates a Windows Desktop shortcut for Jarvis Assistant with the custom robot doll icon.
"""

import os
from pathlib import Path
import win32com.client

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
ICON_PATH = ASSETS_DIR / "jarvis_doll.ico"
VBS_LAUNCHER = BASE_DIR / "run_jarvis_doll.vbs"

desktop = Path(os.path.expanduser("~")) / "Desktop"
shortcut_path = desktop / "Jarvis Assistant.lnk"

shell = win32com.client.Dispatch("WScript.Shell")
shortcut = shell.CreateShortCut(str(shortcut_path))
shortcut.TargetPath = str(VBS_LAUNCHER)
shortcut.WorkingDirectory = str(BASE_DIR)
if ICON_PATH.exists():
    shortcut.IconLocation = f"{ICON_PATH},0"
shortcut.Description = "Jarvis AI Desktop Assistant (Floating Doll)"
shortcut.save()

print(f"Desktop shortcut created at: {shortcut_path}")
