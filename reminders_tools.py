"""
Reminders & Notification tools for Jarvis.
Provides background timers, alarms, and spoken voice alerts.
"""

import threading
import time


def _trigger_reminder(delay_seconds: int, message: str):
    time.sleep(delay_seconds)
    try:
        from plyer import notification
        notification.notify(
            title="Jarvis Reminder",
            message=message,
            app_name="Jarvis",
            timeout=10,
        )
    except Exception:
        pass

    try:
        import voice
        voice.beep()
        voice.speak(f"Reminder: {message}")
    except Exception:
        pass
    print(f"\n[REMINDER ALERT] {message}\n")


def set_reminder(delay_seconds: int, message: str) -> str:
    """Set a background countdown timer that alerts you by voice and notification when done."""
    if delay_seconds <= 0:
        return "Delay must be greater than 0 seconds."

    t = threading.Thread(
        target=_trigger_reminder,
        args=(delay_seconds, message),
        daemon=True,
    )
    t.start()

    minutes = delay_seconds // 60
    secs = delay_seconds % 60
    time_str = f"{minutes}m {secs}s" if minutes else f"{secs} seconds"
    return f"Reminder set for {time_str}: '{message}'."


REGISTRY = {
    "set_reminder": (set_reminder, False),
}

SCHEMAS = [
    {
        "name": "set_reminder",
        "description": "Set a timer/reminder to alert you after a specified number of seconds with a spoken alert.",
        "input_schema": {
            "type": "object",
            "properties": {
                "delay_seconds": {
                    "type": "integer",
                    "description": "Number of seconds until reminder triggers, e.g. 300 for 5 minutes, 60 for 1 minute."
                },
                "message": {
                    "type": "string",
                    "description": "Reminder text, e.g. 'Take a 5-minute eye break' or 'Check the oven'."
                },
            },
            "required": ["delay_seconds", "message"],
        },
    },
]
