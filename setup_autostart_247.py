"""
Configures 24/7 Autostart and Launches Jarvis Assistant Desktop Doll with Watchdog.
1. Installs shortcut in Windows Startup folder (shell:startup)
2. Adds Registry Run entry in HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run
3. Creates Desktop Shortcut and .bat launcher pointing to watchdog supervisor
"""

import os
import shutil
import sys
import winreg
from pathlib import Path
import win32com.client

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
ICON_PATH = ASSETS_DIR / "jarvis_doll.ico"
VBS_LAUNCHER = BASE_DIR / "run_jarvis_doll.vbs"
PYTHONW_EXE = BASE_DIR / ".venv" / "Scripts" / "pythonw.exe"

# 1. Update VBS Launcher to run watchdog
vbs_content = f'''Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "{BASE_DIR}"
WshShell.Run chr(34) & "{PYTHONW_EXE}" & chr(34) & " " & chr(34) & "{BASE_DIR}\\watchdog.py" & chr(34), 1, False
Set WshShell = Nothing
'''
with open(VBS_LAUNCHER, "w", encoding="utf-8") as f:
    f.write(vbs_content)
print(f"[OK] Verified VBS launcher: {VBS_LAUNCHER}")

# 2. Create Desktop Shortcut pointing directly to watchdog
desktop = Path(os.path.expanduser("~")) / "Desktop"
desktop_shortcut = desktop / "Jarvis Assistant.lnk"
shell = win32com.client.Dispatch("WScript.Shell")
shortcut = shell.CreateShortCut(str(desktop_shortcut))
shortcut.TargetPath = str(PYTHONW_EXE)
shortcut.Arguments = "watchdog.py"
shortcut.WorkingDirectory = str(BASE_DIR)
if ICON_PATH.exists():
    shortcut.IconLocation = f"{ICON_PATH},0"
shortcut.Description = "Jarvis AI Desktop Assistant (24/7 Perpetual Doll)"
shortcut.save()
print(f"[OK] Desktop shortcut installed: {desktop_shortcut}")

# Also create/update Start Jarvis.bat launcher right on Desktop
desktop_bat = desktop / "Start Jarvis.bat"
with open(desktop_bat, "w", encoding="utf-8") as f:
    f.write(f'''@echo off
cd /d "{BASE_DIR}"
start "" "{PYTHONW_EXE}" "{BASE_DIR}\\watchdog.py"
''')
print(f"[OK] Desktop batch launcher installed: {desktop_bat}")

# Also update project run_jarvis_doll.bat
project_bat = BASE_DIR / "run_jarvis_doll.bat"
with open(project_bat, "w", encoding="utf-8") as f:
    f.write(f'''@echo off
cd /d "{BASE_DIR}"
start "" "{PYTHONW_EXE}" "{BASE_DIR}\\watchdog.py"
''')

# 3. Install in Windows Startup Folder (runs on every login/boot)
startup_folder = Path(os.environ["APPDATA"]) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
startup_shortcut = startup_folder / "Jarvis Assistant.lnk"
shutil.copyfile(desktop_shortcut, startup_shortcut)
print(f"[OK] Windows Startup shortcut installed: {startup_shortcut}")

# 4. Add to Windows Registry Run Key (HKCU) for 24/7 permanence
reg_key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
try:
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_key_path, 0, winreg.KEY_SET_VALUE) as key:
        winreg.SetValueEx(key, "JarvisDollAssistant", 0, winreg.REG_SZ, f'"{PYTHONW_EXE}" "{BASE_DIR}\\watchdog.py"')
    print("[OK] Registry Run key registered for 24/7 autostart.")
except Exception as e:
    print(f"[WARN] Registry run key error: {e}")
