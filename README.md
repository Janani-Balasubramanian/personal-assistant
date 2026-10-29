# 🤖 Jarvis - Intelligent Personal Assistant & Desktop Companion

An AI-powered desktop assistant and interactive holographic companion built with multi-LLM support, voice capabilities, screen vision, system automation, productivity tools, and local persistence.

---

## ✨ Features

- **Multi-LLM Engine**: Flexible provider support with automatic detection:
  - **Google Gemini** (default, recommended)
  - **Groq** (ultra-fast inference with Llama models)
  - **OpenAI** (GPT-4o / GPT-4o-mini)
  - **xAI / Grok**
  - **Local Ollama** (offline open-source models)
- **Interactive Desktop Doll Widget (`jarvis_doll.py`)**:
  - Floating, draggable 3D-styled animated robot desktop pet.
  - Expressive visual states: `idle`, `listening`, `thinking`, `speaking`.
  - Dynamic speech bubbles and sci-fi audio sound effects.
  - Quick action chips: `☀️ Briefing`, `⏱️ Focus`, `📋 Clip AI`, `📂 Downloads`, `👁️ Screen`, `⚡ System`.
  - Global Windows hotkey: Press **`Ctrl + Alt + J`** from any application to instantly summon or toggle the assistant panel.
  - Right-click settings menu to launch focus sessions, summarize clipboard, check downloads, toggle wake word, or adjust position.
  - Automatically saves on-screen position across reboots (`doll_settings.json`).
- **High-Precision Music & Entertainment Suite (`media_tools.py`)**:
  - Direct video identification: Directly queries YouTube and scrapes exact official video IDs and titles without relying on fragile external web scrapers.
  - Autoplay Launching: Automatically opens `https://www.youtube.com/watch?v={id}&autoplay=1` or Spotify tracks.
  - Media Controls & Volume: Control background playback (`play_pause`, `next`, `prev`, `volume_up`, `volume_down`, `mute`) and set master volume from 0 to 100%.
  - Dedicated Desktop Doll media context menu and quick action chip.
- **WhatsApp Persona & Messaging Suite (`whatsapp_tools.py`)**:
  - **Ghostwriter In Your Voice**: Automatically draft replies mimicking your personal texting voice, habits, and relationship rules (`draft_reply_in_my_voice`).
  - **Relationship-Aware Profiles**: Stores contacts, relationships (family, best friend, work), and custom tone instructions (`whatsapp_persona.json`).
  - **Direct Message Dispatch**: Send or open pre-filled WhatsApp chats directly on Windows Desktop or Web (`send_whatsapp_message`).
- **Productivity & Focus Suite (`focus_tools.py`)**:
  - **Pomodoro Focus Sessions**: Start timed focus sessions (`start_focus_session`) with audio chimes and native Windows toast notifications upon completion.
  - **Productivity Metrics**: Track completed sessions, daily focus hours, and all-time deep work statistics stored in SQLite (`get_focus_stats`).
- **Smart Clipboard AI Copilot (`clipboard_ai_tools.py`)**:
  - Read copied text straight from the clipboard, run AI transformations (`summarize`, `fix_grammar`, `explain`, `extract_tasks`, `to_json`), and copy the result back to the clipboard for instant pasting!
- **Desktop File Finder & Quick Launcher (`desktop_tools.py`)**:
  - Instantly search files across Desktop, Downloads, and Documents (`search_local_files`).
  - View the latest downloaded files (`get_recent_downloads`).
  - Open any file or folder directly in Windows File Explorer (`open_file_or_folder`).
- **Morning Intelligence Briefing (`get_morning_briefing`)**:
  - One-click daily briefing combining real-time local weather, battery and hardware health, calendar events, pending tasks, and focus stats.
- **Voice System (`voice.py`)**:
  - **Wake Word Detection**: Hands-free activation via `"Hey Jarvis"` using `openwakeword`.
  - **Push-to-Talk Mode**: Optional keyboard-triggered voice input.
  - **Local Speech-to-Text**: Fast offline transcription using `faster-whisper`.
  - **Local Text-to-Speech**: Instant offline voice synthesis via `pyttsx3`.
  - **Voice Confirmations**: Sensitive operations prompt for vocal confirmation before executing.
- **Extensive Tool Suite (43+ Tools)**:
  - 🖥️ **Screen Vision (`screen_vision_tools.py`)**: Full screen capture, active window inspection, and multimodal analysis.
  - 🎙️ **Meeting Recorder (`meeting_tools.py`)**: Audio recording with automatic offline local transcription and synced timestamps.
  - ⚙️ **System Automation (`system_tools.py`, `advanced_system_tools.py`)**: Volume, brightness, battery metrics, process management, and app launching.
  - 📝 **Notes & Reminders (`notes_tools.py`, `reminders_tools.py`)**: Fast note taking and scheduled reminder notifications.
  - 📊 **Project Management (`projects_tools.py`)**: SQLite-backed assignment tracking, task deadlines, and progress logs.
  - 🌐 **Web Tools (`web_tools.py`)**: Web search and live site scraping.
  - ⚡ **Custom Actions (`actions_tools.py`)**: User-defined action macros configured via `actions.json`.
- **24/7 High-Availability Supervisor (`watchdog.py`)**:
  - Background supervisor monitors the widget and auto-restarts it within 1–2 seconds if interrupted.
  - Windows autostart installer (`setup_autostart_247.py`) for background boot-up.

---

## 📁 Repository Structure

```text
├── jarvis.py                  # Core agent & tool loop CLI (43+ tools)
├── jarvis_doll.py             # Floating desktop doll GUI widget & hotkey listener
├── voice.py                   # Wake word, Whisper STT & pyttsx3 TTS
├── watchdog.py                # 24/7 background process supervisor
├── setup_autostart_247.py     # Windows autostart configuration utility
│
├── focus_tools.py             # Pomodoro & deep-work focus session tracker
├── clipboard_ai_tools.py      # Smart clipboard AI copilot (summarize, fix grammar, etc.)
├── desktop_tools.py           # Local file finder (Desktop/Downloads/Docs) & quick launcher
├── system_tools.py            # OS control (volume, brightness, apps)
├── advanced_system_tools.py   # Process & resource inspection
├── screen_vision_tools.py     # Screenshot & window vision tools
├── meeting_tools.py           # Audio recording & meeting transcription
├── notes_tools.py             # Local note taking
├── reminders_tools.py         # Reminders and notifications
├── projects_tools.py          # SQLite task/project management
├── web_tools.py               # Web search and scraping
├── actions_tools.py           # Custom action macros
│
├── assets/                    # Doll sprites, icons, and UI images
├── meetings/                  # Recorded audio & transcribed notes
├── notes/                     # Saved text notes
│
├── requirements.txt           # Main dependencies
├── requirements-voice.txt     # Optional voice & wake word dependencies
├── .env.example               # Environment variables template
└── .gitignore                 # Git ignore rules for keys and local logs
```

---

## 🚀 Getting Started

### 1. Prerequisites
- **Python 3.10+** (Python 3.11/3.12 recommended)
- **Git**
- Microphone and speakers (for voice interaction)

### 2. Clone the Repository
```bash
git clone https://github.com/Janani-Balasubramanian/personal-assistant.git
cd personal-assistant
```

### 3. Create a Virtual Environment
```bash
python -m venv .venv

# On Windows (PowerShell):
.venv\Scripts\Activate.ps1

# On Windows (Command Prompt):
.venv\Scripts\activate.bat

# On Linux/macOS:
source .venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
pip install -r requirements-voice.txt
```

### 5. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
copy .env.example .env   # Windows
# or
cp .env.example .env     # Linux / macOS
```

Open `.env` and configure your preferred provider and API key:
```env
# Google Gemini (Default)
JARVIS_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here
JARVIS_MODEL=gemini-2.5-flash
```

---

## 🎮 Running Jarvis

### Option A: Interactive Desktop Doll (GUI Widget)
Run the floating companion on your desktop:
```bash
python jarvis_doll.py
```
- **Global Hotkey**: Press **`Ctrl + Alt + J`** from any open program or game to summon the assistant chat.
- **Left click & drag**: Move the doll anywhere on your screen.
- **Right click**: Open the context menu to launch focus sessions, summarize clipboard, check downloads, toggle wake word, or mute audio.
- **Quick Action Chips**: Click `☀️ Briefing`, `⏱️ Focus`, `📋 Clip AI`, `📂 Downloads`, `👁️ Screen`, or `⚡ System` to run commands instantly.

### Option B: Terminal Agent (CLI)
Run the terminal-based assistant:
```bash
# Standard text mode:
python jarvis.py

# Push-to-talk voice mode (press Enter to speak):
python jarvis.py --voice

# Hands-free wake word mode (say "Hey Jarvis"):
python jarvis.py --voice --wake

# Quick Morning Briefing:
python jarvis.py --briefing
```

### Option C: 24/7 Watchdog Mode
Run the watchdog supervisor to keep the desktop doll running continuously:
```bash
python watchdog.py
```

To configure Jarvis to start automatically when your computer boots up:
```bash
python setup_autostart_247.py
```

---

## 🔒 Privacy & Security

- **API Keys**: Stored exclusively in your local `.env` file and excluded from version control via `.gitignore`. Never commit `.env` or personal credentials to GitHub.
- **Local Voice Processing**: Audio transcription (`faster-whisper`), speech synthesis (`pyttsx3`), and wake word detection (`openwakeword`) run 100% locally on your machine.
- **Safety Confirmations**: Destructive or critical system actions require explicit user approval before execution.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE) (or your preferred license).
