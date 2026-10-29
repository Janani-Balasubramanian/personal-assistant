# 🤖 Jarvis - Intelligent Personal Assistant & Desktop Companion

An AI-powered desktop assistant and interactive holographic companion built with multi-LLM support, voice capabilities, screen vision, system automation, and local persistence.

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
  - Right-click settings menu to toggle voice output, sound effects, wake word, or quit.
  - Automatically saves on-screen position across reboots (`doll_settings.json`).
- **Voice System (`voice.py`)**:
  - **Wake Word Detection**: Hands-free activation via `"Hey Jarvis"` using `openwakeword`.
  - **Push-to-Talk Mode**: Optional keyboard-triggered voice input.
  - **Local Speech-to-Text**: Fast offline transcription using `faster-whisper`.
  - **Local Text-to-Speech**: Instant offline voice synthesis via `pyttsx3`.
  - **Voice Confirmations**: Sensitive operations prompt for vocal confirmation before executing.
- **Extensive Tool Suite**:
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
├── jarvis.py                  # Core agent & tool loop CLI
├── jarvis_doll.py             # Floating desktop doll GUI widget
├── voice.py                   # Wake word, Whisper STT & pyttsx3 TTS
├── watchdog.py                # 24/7 background process supervisor
├── setup_autostart_247.py     # Windows autostart configuration utility
│
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

*(You can also configure Groq, OpenAI, or local Ollama—see `.env.example` for examples.)*

---

## 🎮 Running Jarvis

### Option A: Interactive Desktop Doll (GUI Widget)
Run the floating companion on your desktop:
```bash
python jarvis_doll.py
```
- **Left click & drag**: Move the doll anywhere on your screen.
- **Right click**: Open the settings menu (toggle wake word, mute sound, toggle voice).

### Option B: Terminal Agent (CLI)
Run the terminal-based assistant:
```bash
# Standard text mode:
python jarvis.py

# Push-to-talk voice mode (press Enter to speak):
python jarvis.py --voice

# Hands-free wake word mode (say "Hey Jarvis"):
python jarvis.py --voice --wake
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
