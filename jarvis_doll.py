"""
Jarvis Desktop Doll & Holographic Assistant.

A floating, interactive 3D robot desktop pet/doll docked in the bottom-right
corner of your laptop screen. Operates completely outside the terminal!
"""

import datetime as dt
import json
import math
import os
import queue
import re
import sys
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import messagebox
from PIL import Image, ImageTk

# Base directories
BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
CONFIG_FILE = BASE_DIR / "doll_settings.json"

# In pythonw.exe, stdout and stderr are None; redirect them so prints don't crash
if sys.stdout is None:
    try:
        sys.stdout = open(BASE_DIR / "doll_stdout.log", "a", encoding="utf-8", errors="replace", buffering=1)
    except Exception:
        import io
        sys.stdout = io.StringIO()
elif hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

if sys.stderr is None:
    try:
        sys.stderr = open(BASE_DIR / "doll_stderr.log", "a", encoding="utf-8", errors="replace", buffering=1)
    except Exception:
        import io
        sys.stderr = io.StringIO()
elif hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


# Try importing sound module for Windows sci-fi feedback
try:
    import winsound
    HAVE_WINSOUND = True
except ImportError:
    HAVE_WINSOUND = False

# Import Jarvis Core and Voice
import sqlite3
import jarvis
import voice

try:
    jarvis.db = sqlite3.connect(jarvis.DB_PATH, check_same_thread=False)
    jarvis.db.row_factory = sqlite3.Row
except Exception:
    pass

# Chromakey transparency color (Windows removes all pixels matching this color)
TRANS_HEX = "#ff00ff"
TRANS_RGB = (255, 0, 255)


# --------------------------------------------------------------------------
# Settings Persistence
# --------------------------------------------------------------------------

DEFAULT_SETTINGS = {
    "x": None,
    "y": None,
    "wake_word": True,
    "voice_output": True,
    "sound_fx": True,
    "mic_threshold": None,
}


def load_settings() -> dict:
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {**DEFAULT_SETTINGS, **data}
        except Exception:
            pass
    return DEFAULT_SETTINGS.copy()


def save_settings(settings: dict) -> None:
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
    except Exception as e:
        print(f"Error saving settings: {e}")


# --------------------------------------------------------------------------
# Sound Effects (Async, non-blocking)
# --------------------------------------------------------------------------

def play_sound(sound_type: str) -> None:
    if not HAVE_WINSOUND:
        return

    def _beep():
        try:
            if sound_type == "wake":
                # High-tech rising two-tone chime
                winsound.Beep(900, 70)
                winsound.Beep(1350, 90)
            elif sound_type == "done":
                # Gentle descending resolution tone
                winsound.Beep(1100, 50)
                winsound.Beep(850, 70)
            elif sound_type == "click":
                # Crisp tick
                winsound.Beep(1600, 20)
            elif sound_type == "alert":
                # Warning prompt
                winsound.Beep(700, 80)
                winsound.Beep(550, 100)
        except Exception:
            pass

    threading.Thread(target=_beep, daemon=True).start()


# --------------------------------------------------------------------------
# Holographic Assistant Panel Window
# --------------------------------------------------------------------------

class HolographicPanel(tk.Toplevel):
    """
    Sleek cyberpunk/glassmorphism holographic dashboard that docks beside
    the floating robot doll.
    """

    def __init__(self, master_doll, on_send_callback, on_mic_callback):
        super().__init__(master_doll)
        self.master_doll = master_doll
        self.on_send_callback = on_send_callback
        self.on_mic_callback = on_mic_callback

        self.title("Jarvis AI Assistant")
        self.overrideredirect(True)
        self.wm_attributes("-topmost", True)
        self.configure(bg="#0b1120")

        self.width = 380
        self.height = 490

        # Confirmation state handler
        self.confirm_event = None
        self.confirm_result = False

        self._build_ui()
        self.withdraw()  # Hidden initially until clicked or invoked

    def _build_ui(self):
        # Outer border frame with glowing cyan edge
        self.outer_frame = tk.Frame(self, bg="#0ea5e9", bd=1)
        self.outer_frame.pack(fill="both", expand=True)

        self.inner_frame = tk.Frame(self.outer_frame, bg="#090d16")
        self.inner_frame.pack(fill="both", expand=True, padx=1, pady=1)

        # Header bar
        self.header = tk.Frame(self.inner_frame, bg="#0f172a", height=38)
        self.header.pack(fill="x", side="top")
        self.header.pack_propagate(False)

        # Drag handler for panel
        self.header.bind("<ButtonPress-1>", self._start_drag)
        self.header.bind("<B1-Motion>", self._on_drag)

        title_lbl = tk.Label(
            self.header,
            text="⚡ JARVIS INTELLIGENCE",
            bg="#0f172a",
            fg="#38bdf8",
            font=("Segoe UI", 9, "bold")
        )
        title_lbl.pack(side="left", padx=10)
        title_lbl.bind("<ButtonPress-1>", self._start_drag)
        title_lbl.bind("<B1-Motion>", self._on_drag)

        # Status badge pill
        self.status_badge = tk.Label(
            self.header,
            text="● READY",
            bg="#0369a1",
            fg="#e0f2fe",
            font=("Segoe UI", 7, "bold"),
            padx=6,
            pady=1
        )
        self.status_badge.pack(side="left", padx=5)

        # Close / Minimize button
        close_btn = tk.Button(
            self.header,
            text="✕",
            bg="#0f172a",
            fg="#94a3b8",
            activebackground="#ef4444",
            activeforeground="#ffffff",
            bd=0,
            font=("Segoe UI", 9, "bold"),
            cursor="hand2",
            command=self.hide_panel
        )
        close_btn.pack(side="right", padx=8)

        # Quick action chips
        chips_frame = tk.Frame(self.inner_frame, bg="#090d16")
        chips_frame.pack(fill="x", padx=8, pady=(6, 4))

        quick_actions = [
            ("☀️ Briefing", lambda: self.on_send_callback("give me my morning briefing")),
            ("⏱️ Focus", lambda: self.on_send_callback("start a 25 minute focus session for deep work")),
            ("📋 Clip AI", lambda: self.on_send_callback("summarize what is on my clipboard")),
            ("📂 Downloads", lambda: self.on_send_callback("show my recent downloads")),
            ("👁️ Screen", lambda: self.on_send_callback("look at my screen and tell me what you see")),
            ("⚡ System", lambda: self.on_send_callback("check system status and battery")),
        ]
        for text, cmd in quick_actions:
            btn = tk.Button(
                chips_frame,
                text=text,
                bg="#1e293b",
                fg="#94a3b8",
                activebackground="#0284c7",
                activeforeground="#ffffff",
                bd=0,
                font=("Segoe UI", 8),
                padx=6,
                pady=2,
                cursor="hand2",
                command=cmd
            )
            btn.pack(side="left", padx=2)

        self.meeting_btn = tk.Button(
            chips_frame,
            text="🔴 Meeting",
            bg="#1e293b",
            fg="#f87171",
            activebackground="#dc2626",
            activeforeground="#ffffff",
            bd=0,
            font=("Segoe UI", 8, "bold"),
            padx=6,
            pady=2,
            cursor="hand2",
            command=self._toggle_meeting
        )
        self.meeting_btn.pack(side="left", padx=2)

        # Conversation log area
        chat_frame = tk.Frame(self.inner_frame, bg="#090d16")
        chat_frame.pack(fill="both", expand=True, padx=8, pady=2)

        self.chat_text = tk.Text(
            chat_frame,
            bg="#0f172a",
            fg="#f8fafc",
            font=("Segoe UI", 9),
            bd=0,
            wrap="word",
            padx=8,
            pady=8,
            selectbackground="#0284c7"
        )
        self.chat_scroll = tk.Scrollbar(chat_frame, command=self.chat_text.yview, bg="#0f172a")
        self.chat_text.configure(yscrollcommand=self.chat_scroll.set)

        self.chat_scroll.pack(side="right", fill="y")
        self.chat_text.pack(side="left", fill="both", expand=True)

        # Configure chat tags
        self.chat_text.tag_configure("user", foreground="#38bdf8", font=("Segoe UI", 9, "bold"))
        self.chat_text.tag_configure("jarvis", foreground="#f1f5f9", font=("Segoe UI", 9))
        self.chat_text.tag_configure("tool", foreground="#a855f7", font=("Segoe UI", 8, "italic"))
        self.chat_text.tag_configure("time", foreground="#64748b", font=("Segoe UI", 7))
        self.chat_text.tag_configure("alert", foreground="#fbbf24", font=("Segoe UI", 8, "bold"))

        # Confirmation card frame (hidden by default)
        self.confirm_frame = tk.Frame(self.inner_frame, bg="#1e1b4b", bd=1)
        self.confirm_lbl = tk.Label(
            self.confirm_frame,
            text="",
            bg="#1e1b4b",
            fg="#e0e7ff",
            font=("Segoe UI", 8, "bold"),
            wraplength=350,
            justify="left",
            padx=6,
            pady=4
        )
        self.confirm_lbl.pack(fill="x")

        btn_row = tk.Frame(self.confirm_frame, bg="#1e1b4b")
        btn_row.pack(fill="x", pady=(2, 6), padx=6)

        self.btn_allow = tk.Button(
            btn_row,
            text="✅ Approve",
            bg="#16a34a",
            fg="#ffffff",
            activebackground="#22c55e",
            bd=0,
            font=("Segoe UI", 8, "bold"),
            padx=10,
            pady=2,
            cursor="hand2",
            command=lambda: self._resolve_confirm(True)
        )
        self.btn_allow.pack(side="left", padx=4)

        self.btn_deny = tk.Button(
            btn_row,
            text="❌ Deny",
            bg="#dc2626",
            fg="#ffffff",
            activebackground="#ef4444",
            bd=0,
            font=("Segoe UI", 8, "bold"),
            padx=10,
            pady=2,
            cursor="hand2",
            command=lambda: self._resolve_confirm(False)
        )
        self.btn_deny.pack(side="left", padx=4)

        # Bottom Input Area
        bottom_frame = tk.Frame(self.inner_frame, bg="#090d16")
        bottom_frame.pack(fill="x", side="bottom", padx=8, pady=(4, 8))

        # Glowing Mic Button
        self.mic_btn = tk.Button(
            bottom_frame,
            text="🎙️",
            bg="#0284c7",
            fg="#ffffff",
            activebackground="#38bdf8",
            activeforeground="#000000",
            bd=0,
            font=("Segoe UI", 11),
            width=3,
            cursor="hand2",
            command=self.on_mic_callback
        )
        self.mic_btn.pack(side="left", padx=(0, 6))

        # Text Input Entry
        self.entry_var = tk.StringVar()
        self.entry = tk.Entry(
            bottom_frame,
            textvariable=self.entry_var,
            bg="#1e293b",
            fg="#f8fafc",
            insertbackground="#38bdf8",
            font=("Segoe UI", 9),
            bd=0
        )
        self.entry.pack(side="left", fill="x", expand=True, ipady=4, padx=(0, 6))
        self.entry.bind("<Return>", self._on_enter)

        # Send Button
        send_btn = tk.Button(
            bottom_frame,
            text="➤",
            bg="#0284c7",
            fg="#ffffff",
            activebackground="#38bdf8",
            bd=0,
            font=("Segoe UI", 10, "bold"),
            width=3,
            cursor="hand2",
            command=self._on_enter
        )
        send_btn.pack(side="right")

        # Initial welcome message in conversation
        self.add_message("Jarvis", "Jarvis online and ready. Click the mic or talk to me!", "jarvis")

    def _start_drag(self, event):
        self._drag_start_x = event.x
        self._drag_start_y = event.y

    def _on_drag(self, event):
        x = self.winfo_x() + (event.x - self._drag_start_x)
        y = self.winfo_y() + (event.y - self._drag_start_y)
        self.geometry(f"+{x}+{y}")

    def _on_enter(self, event=None):
        text = self.entry_var.get().strip()
        if text:
            self.entry_var.set("")
            self.on_send_callback(text)

    def _toggle_meeting(self):
        import meeting_tools
        if not meeting_tools.recorder.is_recording:
            self.meeting_btn.configure(bg="#dc2626", fg="#ffffff", text="⏹️ Stop Meeting")
            self.on_send_callback("start listening to my meeting and recording notes")
        else:
            self.meeting_btn.configure(bg="#1e293b", fg="#f87171", text="🔴 Meeting")
            self.on_send_callback("stop meeting recording, transcribe it, and give me the summary and action items")

    def add_message(self, sender: str, text: str, tag: str = "jarvis"):
        self.chat_text.configure(state="normal")
        time_str = dt.datetime.now().strftime("%H:%M")

        if sender == "You":
            self.chat_text.insert("end", f"\nYou ({time_str}):\n", ("user", "time"))
            self.chat_text.insert("end", f"{text}\n")
        elif sender == "Tool":
            self.chat_text.insert("end", f"  ⚙️ {text}\n", "tool")
        else:
            self.chat_text.insert("end", f"\nJarvis ({time_str}):\n", ("jarvis", "time"))
            self.chat_text.insert("end", f"{text}\n")

        self.chat_text.see("end")
        self.chat_text.configure(state="disabled")

    def set_status(self, status: str):
        colors = {
            "Ready": ("#0369a1", "● READY"),
            "Listening": ("#059669", "● LISTENING..."),
            "Thinking": ("#7c3aed", "● THINKING..."),
            "Speaking": ("#d97706", "● SPEAKING..."),
        }
        bg, text = colors.get(status, ("#0369a1", f"● {status.upper()}"))
        self.status_badge.configure(bg=bg, text=text)

        if status == "Listening":
            self.mic_btn.configure(bg="#10b981", text="🔊")
        else:
            self.mic_btn.configure(bg="#0284c7", text="🎙️")

    def prompt_confirmation(self, action_name: str, args: dict, event: threading.Event, container: list):
        self.confirm_event = event
        self.confirm_container = container
        detail = " ".join(f"{k}={v}" for k, v in args.items())
        self.confirm_lbl.configure(text=f"⚠️ Allow Jarvis to run '{action_name}'?\n({detail})")
        self.confirm_frame.pack(fill="x", padx=8, pady=(0, 4), before=self.inner_frame.pack_slaves()[-1])
        self.show_panel()

    def _resolve_confirm(self, approved: bool):
        self.confirm_frame.pack_forget()
        if self.confirm_event and self.confirm_container:
            self.confirm_container.append(approved)
            self.confirm_event.set()
        self.confirm_event = None

    def toggle_panel(self):
        if self.winfo_viewable():
            self.hide_panel()
        else:
            self.show_panel()

    def show_panel(self):
        # Reposition panel cleanly to the left or above the doll
        doll_x = self.master_doll.winfo_x()
        doll_y = self.master_doll.winfo_y()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()

        target_x = doll_x - self.width - 12
        if target_x < 10:
            target_x = doll_x + self.master_doll.winfo_width() + 12
        if target_x + self.width > screen_w:
            target_x = screen_w - self.width - 10

        target_y = doll_y - (self.height - self.master_doll.winfo_height())
        if target_y < 10:
            target_y = 10
        if target_y + self.height > screen_h - 45:
            target_y = screen_h - self.height - 45

        self.geometry(f"{self.width}x{self.height}+{target_x}+{target_y}")
        self.deiconify()
        self.lift()
        self.entry.focus_set()

    def hide_panel(self):
        self.withdraw()


# --------------------------------------------------------------------------
# Floating Mini Speech Bubble (when panel is minimized)
# --------------------------------------------------------------------------

class SpeechBubble(tk.Toplevel):
    """
    A cute floating speech bubble card that appears right beside the doll
    when Jarvis replies by voice while the main panel is hidden.
    """

    def __init__(self, master):
        super().__init__(master)
        self.overrideredirect(True)
        self.wm_attributes("-topmost", True)
        self.configure(bg="#0ea5e9")
        self.withdraw()
        self._dismiss_job = None

        self.inner = tk.Frame(self, bg="#0f172a", padx=10, pady=8)
        self.inner.pack(fill="both", expand=True, padx=1, pady=1)

        self.lbl = tk.Label(
            self.inner,
            text="",
            bg="#0f172a",
            fg="#f8fafc",
            font=("Segoe UI", 9),
            wraplength=260,
            justify="left"
        )
        self.lbl.pack()
        self.inner.bind("<Button-1>", lambda e: self.hide_bubble())
        self.lbl.bind("<Button-1>", lambda e: self.hide_bubble())

    def show_text(self, text: str, doll_x: int, doll_y: int, doll_h: int):
        if self._dismiss_job:
            self.after_cancel(self._dismiss_job)

        # Truncate text if very long for quick glance
        display_text = text if len(text) < 220 else text[:215] + "..."
        self.lbl.configure(text=f"🤖 {display_text}")

        self.update_idletasks()
        bw = self.winfo_reqwidth()
        bh = self.winfo_reqheight()

        # Position to the left of the doll's head
        bx = doll_x - bw - 10
        by = max(20, doll_y - bh + 40)
        self.geometry(f"+{bx}+{by}")
        self.deiconify()
        self.lift()

        # Auto hide after 7 seconds
        self._dismiss_job = self.after(7000, self.hide_bubble)

    def hide_bubble(self):
        self.withdraw()


# --------------------------------------------------------------------------
# Desktop Doll Widget Window
# --------------------------------------------------------------------------

class DollWidget(tk.Tk):
    """
    The floating transparent 3D cute robot doll sitting in the bottom-right corner.
    """

    def __init__(self):
        super().__init__()
        self.settings = load_settings()

        self.title("Jarvis Doll")
        self.overrideredirect(True)
        self.wm_attributes("-topmost", True)
        self.wm_attributes("-transparentcolor", TRANS_HEX)
        self.configure(bg=TRANS_HEX)

        # Dimensions of the doll widget window
        self.widget_w = 175
        self.widget_h = 215

        # Initialize position
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        default_x = screen_w - self.widget_w - 25
        default_y = screen_h - self.widget_h - 70  # Comfortably above Windows taskbar

        pos_x = self.settings.get("x") or default_x
        pos_y = self.settings.get("y") or default_y
        # Validate coordinates inside screen
        pos_x = max(10, min(pos_x, screen_w - self.widget_w - 10))
        pos_y = max(10, min(pos_y, screen_h - self.widget_h - 30))

        self.geometry(f"{self.widget_w}x{self.widget_h}+{pos_x}+{pos_y}")

        # State management
        self.current_state = "idle"  # idle, listening, thinking, speaking
        self.bob_step = 0.0
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.drag_moved = False

        # Load transparent pre-composited frames
        self.frames = {}
        self._load_frames()

        # Canvas for rendering the doll and bobbing shadow
        self.canvas = tk.Canvas(
            self,
            width=self.widget_w,
            height=self.widget_h,
            bg=TRANS_HEX,
            highlightthickness=0,
            bd=0
        )
        self.canvas.pack(fill="both", expand=True)

        # Canvas elements
        self.shadow_id = self.canvas.create_oval(35, 195, 140, 207, fill="#1e293b", outline="")
        self.doll_img_id = self.canvas.create_image(2, 6, anchor="nw", image=self.frames["idle"])

        # Bindings for dragging, clicking, and context menu
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Button-3>", self._show_context_menu)

        # Floating speech bubble
        self.speech_bubble = SpeechBubble(self)

        # Holographic control panel
        self.panel = HolographicPanel(self, self.send_user_message, self.trigger_push_to_talk)

        # Context menu
        self._build_context_menu()

        # Background Voice & Assistant Thread
        self.msg_queue = queue.Queue()
        self.audio_lock = threading.Lock()
        self.voice_running = True
        self.is_recording = False
        self.wake_active = self.settings.get("wake_word", True)

        # Hook Jarvis confirmation to GUI
        jarvis.CONFIRM = self._gui_confirm

        # Start animation loop
        self._animate_bob()

        # Force window visibility and bring to topmost
        self.deiconify()
        self.lift()
        self.wm_attributes("-topmost", True)
        self.after(100, self._force_window_topmost)

        # Start queue processor
        self.after(50, self._process_queue)

        # Start background wake word thread
        self.voice_thread = threading.Thread(target=self._voice_loop, daemon=True)
        self.voice_thread.start()

        # Start global hotkey listener (Ctrl+Alt+J)
        self.hotkey_thread = threading.Thread(target=self._listen_global_hotkey, daemon=True)
        self.hotkey_thread.start()

        # Greet user softly on launch
        self.after(600, self._startup_greeting)

    def _force_window_topmost(self):
        self.deiconify()
        self.lift()
        self.wm_attributes("-topmost", True)
        try:
            import win32gui, win32con
            hwnd = self.winfo_id()
            parent = win32gui.GetParent(hwnd)
            target = parent if parent else hwnd
            win32gui.ShowWindow(target, win32con.SW_SHOW)
            win32gui.SetWindowPos(target, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                                  win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW)
        except Exception:
            pass


    def _load_frames(self):
        for state in ["idle", "listening", "thinking", "speaking"]:
            img_path = ASSETS_DIR / f"doll_{state}_widget.png"
            if img_path.exists():
                pil_img = Image.open(img_path)
            else:
                pil_img = Image.open(ASSETS_DIR / "doll_idle_widget.png")
            self.frames[state] = ImageTk.PhotoImage(pil_img)

    def _build_context_menu(self):
        self.menu = tk.Menu(self, tearoff=0, bg="#0f172a", fg="#f8fafc", activebackground="#0284c7")
        self.menu.add_command(label="🎙️ Push-to-Talk (Speak)", command=self.trigger_push_to_talk)
        self.menu.add_command(label="💬 Open Chat Panel", command=self.panel.show_panel)
        
        # Messaging apps quick access submenu
        msg_menu = tk.Menu(self.menu, tearoff=0, bg="#0f172a", fg="#f8fafc", activebackground="#0284c7")
        msg_menu.add_command(label="🟢 WhatsApp", command=lambda: self.send_user_message("open whatsapp"))
        msg_menu.add_command(label="✈️ Telegram", command=lambda: self.send_user_message("open telegram"))
        msg_menu.add_command(label="👾 Discord", command=lambda: self.send_user_message("open discord"))
        msg_menu.add_command(label="💼 Slack", command=lambda: self.send_user_message("open slack"))
        msg_menu.add_command(label="👥 Teams", command=lambda: self.send_user_message("open teams"))
        msg_menu.add_command(label="✉️ Gmail", command=lambda: self.send_user_message("open gmail"))
        self.menu.add_cascade(label="💬 Messaging Apps", menu=msg_menu)

        self.menu.add_separator()
        self.menu.add_command(label="☀️ Morning Briefing", command=lambda: self.send_user_message("give me my morning briefing"))
        self.menu.add_command(label="⏱️ Start 25m Focus Session", command=lambda: self.send_user_message("start a 25 minute focus session"))
        self.menu.add_command(label="📋 AI Summarize Clipboard", command=lambda: self.send_user_message("summarize what is on my clipboard"))
        self.menu.add_command(label="📂 Recent Downloads", command=lambda: self.send_user_message("show my recent downloads"))
        self.menu.add_command(label="⚡ System Status", command=lambda: self.send_user_message("check system status and battery"))
        self.menu.add_command(label="👁️ Screen Vision", command=lambda: self.send_user_message("look at my screen and tell me what you see"))
        self.menu.add_command(label="🔴 Record Meeting / Call", command=lambda: self.send_user_message("start listening to my meeting and take notes"))
        self.menu.add_command(label="⏹️ Stop & Summarize Meeting", command=lambda: self.send_user_message("stop meeting recording, transcribe it, and give me the summary and action items"))
        self.menu.add_separator()
        self.menu.add_command(label="👂 Toggle 'Hey Jarvis' Wake Word", command=self.toggle_wake_word)
        self.menu.add_command(label="📍 Reset to Bottom-Right Corner", command=self.reset_position)
        self.menu.add_separator()
        self.menu.add_command(label="❌ Exit Jarvis", command=self.quit_app)

    def _show_context_menu(self, event):
        play_sound("click")
        self.menu.post(event.x_root, event.y_root)

    def _on_press(self, event):
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        self.drag_moved = False

    def _on_drag(self, event):
        dx = event.x - self.drag_start_x
        dy = event.y - self.drag_start_y
        if abs(dx) > 3 or abs(dy) > 3:
            self.drag_moved = True
            new_x = self.winfo_x() + dx
            new_y = self.winfo_y() + dy
            self.geometry(f"+{new_x}+{new_y}")

    def _on_release(self, event):
        if not self.drag_moved:
            # Single click toggles holographic panel!
            play_sound("click")
            self.panel.toggle_panel()
        else:
            # Save new dragged position
            self.settings["x"] = self.winfo_x()
            self.settings["y"] = self.winfo_y()
            save_settings(self.settings)

    def _animate_bob(self):
        """Smooth vertical sinusoidal bobbing animation for realistic floating pet effect."""
        self.bob_step += 0.08
        dy = int(round(3.8 * math.sin(self.bob_step)))

        # Update doll vertical position
        self.canvas.coords(self.doll_img_id, 2, 8 + dy)

        # Update shadow size in inverse phase (widens when closer to ground, contracts when higher)
        spread = -int(round(dy * 1.5))
        self.canvas.coords(self.shadow_id, 35 - spread, 200, 140 + spread, 208)

        self.after(35, self._animate_bob)

    def set_doll_state(self, state: str):
        self.current_state = state
        frame = self.frames.get(state, self.frames["idle"])
        self.canvas.itemconfig(self.doll_img_id, image=frame)
        self.panel.set_status(state.capitalize())

    def reset_position(self):
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        rx = screen_w - self.widget_w - 20
        ry = screen_h - self.widget_h - 48
        self.geometry(f"+{rx}+{ry}")
        self.settings["x"] = rx
        self.settings["y"] = ry
        save_settings(self.settings)

    def toggle_wake_word(self):
        self.wake_active = not self.wake_active
        self.settings["wake_word"] = self.wake_active
        save_settings(self.settings)
        msg = f"Wake Word is now {'ENABLED (Say Hey Jarvis)' if self.wake_active else 'DISABLED (Use Push-to-Talk)'}"
        self.panel.add_message("Jarvis", msg)
        play_sound("done")

    def _startup_greeting(self):
        play_sound("wake")
        self.set_doll_state("speaking")
        welcome = "Jarvis online. I'm right here in your corner whenever you need me!"
        self.speech_bubble.show_text(welcome, self.winfo_x(), self.winfo_y(), self.widget_h)
        self.after(2200, lambda: self.set_doll_state("idle"))

    # ----------------------------------------------------------------------
    # Message Dispatching & Processing
    # ----------------------------------------------------------------------

    def send_user_message(self, text: str):
        if not text.strip():
            return
        self.panel.add_message("You", text, "user")
        self.set_doll_state("thinking")
        play_sound("click")

        # Run assistant ask in background thread
        threading.Thread(target=self._run_jarvis_ask, args=(text,), daemon=True).start()

    def _run_jarvis_ask(self, text: str):
        turn_start = 0
        try:
            # Maintain conversation context
            if not hasattr(self, "conversation_history"):
                self.conversation_history = []
            turn_start = len(self.conversation_history)
            self.conversation_history.append({"role": "user", "content": text})

            # Ask LLM (executes tool loops)
            response = jarvis.ask(self.conversation_history)

            # Keep only clean conversational dialogue turns (user + assistant text) in persistent history
            # This completely avoids token bloat and prevents tool-call slicing bugs across turns
            clean_history = []
            for m in self.conversation_history:
                if isinstance(m, dict) and m.get("role") in ("user", "assistant") and m.get("content"):
                    clean_history.append({"role": m["role"], "content": m["content"]})
                elif hasattr(m, "role") and getattr(m, "role", "") == "assistant" and getattr(m, "content", ""):
                    clean_history.append({"role": "assistant", "content": m.content})

            if len(clean_history) > 20:
                clean_history = clean_history[-16:]
            self.conversation_history = clean_history

            self.msg_queue.put(("response", response))
        except Exception as e:
            if hasattr(self, "conversation_history") and len(self.conversation_history) > turn_start:
                del self.conversation_history[turn_start:]
            self.msg_queue.put(("error", str(e)))

    def _gui_confirm(self, name: str, args: dict) -> bool:
        """Called by Jarvis tool loop when an action needs user confirmation."""
        event = threading.Event()
        container = []
        play_sound("alert")

        # Dispatch confirmation prompt to UI
        self.msg_queue.put(("confirm", (name, args, event, container)))

        # Wait for user click or voice confirmation
        event.wait(timeout=30)
        return container[0] if container else False

    def _process_queue(self):
        try:
            while not self.msg_queue.empty():
                item = self.msg_queue.get_nowait()
                mtype, data = item

                if mtype == "toggle_panel":
                    self.panel.toggle_panel()
                elif mtype == "state":
                    self.set_doll_state(data)
                elif mtype == "response":
                    self.set_doll_state("speaking")
                    self.panel.add_message("Jarvis", data, "jarvis")

                    # If main panel is hidden, show cute floating speech bubble
                    if not self.panel.winfo_viewable():
                        self.speech_bubble.show_text(data, self.winfo_x(), self.winfo_y(), self.widget_h)

                    # Speak aloud in background thread
                    if self.settings.get("voice_output", True):
                        threading.Thread(target=self._speak_reply, args=(data,), daemon=True).start()
                    else:
                        play_sound("done")
                        self.set_doll_state("idle")

                elif mtype == "error":
                    self.set_doll_state("idle")
                    self.panel.add_message("Jarvis", f"⚠️ Error: {data}", "alert")
                    play_sound("alert")

                elif mtype == "confirm":
                    name, args, event, container = data
                    self.panel.prompt_confirmation(name, args, event, container)

                elif mtype == "tool":
                    self.panel.add_message("Tool", data, "tool")

        except Exception as e:
            print(f"Queue processing error: {e}")

        self.after(50, self._process_queue)

    def _speak_reply(self, text: str):
        try:
            voice.speak(text)
        except Exception as e:
            print(f"Speech error: {e}")
        finally:
            play_sound("done")
            self.msg_queue.put(("state", "idle"))

    # ----------------------------------------------------------------------
    # Voice Input & Wake Word Engine
    # ----------------------------------------------------------------------

    def trigger_push_to_talk(self):
        if self.is_recording:
            return
        threading.Thread(target=self._record_and_transcribe, daemon=True).start()

    def _record_and_transcribe(self):
        if not self.audio_lock.acquire(blocking=False):
            return  # audio hardware currently busy
        self.is_recording = True
        self.msg_queue.put(("state", "listening"))
        play_sound("wake")

        try:
            time.sleep(0.15)  # allow PortAudio device release
            threshold = voice._threshold if hasattr(voice, "_threshold") else 0.02
            audio = voice.record_utterance(threshold)
            if audio is not None:
                self.msg_queue.put(("state", "thinking"))
                text = voice.transcribe(audio)
                if text:
                    self.send_user_message(text)
                else:
                    self.msg_queue.put(("state", "idle"))
            else:
                self.msg_queue.put(("state", "idle"))
        except Exception as e:
            self.msg_queue.put(("error", f"Audio capture failed: {e}"))
            self.msg_queue.put(("state", "idle"))
        finally:
            self.is_recording = False
            time.sleep(0.25)
            self.audio_lock.release()

    def _voice_loop(self):
        """Background listener for 'Hey Jarvis' wake word with synchronized audio locking."""
        time.sleep(2)
        while self.voice_running:
            if not self.wake_active or self.is_recording:
                time.sleep(0.5)
                continue

            if not self.audio_lock.acquire(blocking=False):
                time.sleep(0.5)
                continue

            try:
                detected = voice.wait_for_wake_word(threshold=0.55)
            except Exception:
                detected = False
            finally:
                self.audio_lock.release()
                time.sleep(0.25)

            if detected and self.wake_active and not self.is_recording:
                self._record_and_transcribe()

    def _listen_global_hotkey(self):
        """Listen for Ctrl+Alt+J anywhere in Windows to toggle the Jarvis chat panel."""
        if sys.platform != "win32":
            return
        try:
            import ctypes
            from ctypes import wintypes
            user32 = ctypes.windll.user32
            MOD_ALT = 0x0001
            MOD_CONTROL = 0x0002
            MOD_NOREPEAT = 0x4000
            VK_J = 0x4A  # Virtual Key for 'J'
            HOTKEY_ID = 9991

            if user32.RegisterHotKey(None, HOTKEY_ID, MOD_CONTROL | MOD_ALT | MOD_NOREPEAT, VK_J):
                msg = wintypes.MSG()
                while self.voice_running:
                    if user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
                        if msg.message == 0x0312 and msg.wParam == HOTKEY_ID:
                            self.msg_queue.put(("toggle_panel", None))
                        user32.TranslateMessage(ctypes.byref(msg))
                        user32.DispatchMessageW(ctypes.byref(msg))
                user32.UnregisterHotKey(None, HOTKEY_ID)
        except Exception:
            pass

    def quit_app(self):
        self.voice_running = False
        save_settings(self.settings)
        try:
            (BASE_DIR / "exit.flag").write_text("exit")
        except Exception:
            pass
        self.destroy()
        sys.exit(0)


# --------------------------------------------------------------------------
# Main Entry Point
# --------------------------------------------------------------------------

def main():
    try:
        os.chdir(BASE_DIR)
        flag = BASE_DIR / "exit.flag"
        if flag.exists():
            try:
                flag.unlink()
            except Exception:
                pass
        app = DollWidget()
        app.mainloop()
    except Exception as e:
        with open(BASE_DIR / "doll_crash.log", "a", encoding="utf-8") as f:
            import traceback
            traceback.print_exc(file=f)



if __name__ == "__main__":
    main()
