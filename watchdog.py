"""
Jarvis 24/7 Watchdog Supervisor.
Keeps the Jarvis Desktop Doll running perpetually in the bottom-right corner.
If the doll process ever closes or crashes unexpectedly, the watchdog immediately
restarts it within 1-2 seconds.
"""

import os
import subprocess
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PYTHONW = str(BASE_DIR / ".venv" / "Scripts" / "pythonw.exe")
FLAG_FILE = BASE_DIR / "exit.flag"
LOG_FILE = BASE_DIR / "watchdog.log"


def log(msg: str):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    except Exception:
        pass


def main():
    os.chdir(BASE_DIR)

    # Clear old exit flag if present on fresh boot/start
    if FLAG_FILE.exists():
        try:
            FLAG_FILE.unlink()
        except Exception:
            pass

    log("Watchdog started. Monitoring Jarvis Desktop Doll 24/7.")

    while True:
        if FLAG_FILE.exists():
            log("Deliberate exit requested by user. Watchdog shutting down.")
            break

        log("Spawning jarvis_doll.py...")
        proc = subprocess.Popen(
            [PYTHONW, str(BASE_DIR / "jarvis_doll.py")],
            cwd=str(BASE_DIR),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # Wait for the doll process
        proc.wait()

        # If user right-clicked and clicked 'Exit Jarvis', FLAG_FILE will exist
        if FLAG_FILE.exists():
            log(f"Jarvis Doll exited normally (code {proc.returncode}). Watchdog exiting.")
            break

        log(f"Jarvis Doll terminated unexpectedly with code {proc.returncode}. Restarting in 2s...")
        time.sleep(2)


if __name__ == "__main__":
    main()
