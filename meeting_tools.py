"""
Meeting Intelligence & Live Note-Taking Tools for Jarvis.

Enables Jarvis to attend, listen to, and record live meetings, video calls, lectures,
or discussions. Automatically transcribes with faster-whisper, generates structured
meeting minutes, extracts action items and deadlines into tasks, and saves notes.
"""

import datetime as dt
import os
import threading
import time
from pathlib import Path
import numpy as np
import scipy.io.wavfile as wavfile
import sounddevice as sd

BASE_DIR = Path(__file__).resolve().parent
NOTES_DIR = BASE_DIR / "notes"
MEETINGS_DIR = BASE_DIR / "meetings"
NOTES_DIR.mkdir(parents=True, exist_ok=True)
MEETINGS_DIR.mkdir(parents=True, exist_ok=True)

SAMPLE_RATE = 16000
BLOCK_SIZE = 1600  # 100ms per block


class MeetingRecorder:
    def __init__(self):
        self.is_recording = False
        self.audio_chunks = []
        self.start_time = 0.0
        self.meeting_title = "Meeting"
        self.stop_event = threading.Event()
        self.worker_thread = None
        self.lock = threading.Lock()

    def start(self, title: str = "Meeting", auto_stop_minutes: float = 0.0) -> str:
        with self.lock:
            if self.is_recording:
                elapsed = int((time.time() - self.start_time) / 60)
                return f"A meeting recording is already in progress: '{self.meeting_title}' (running for {elapsed} min)."

            self.is_recording = True
            self.meeting_title = title.strip() or "Meeting"
            self.start_time = time.time()
            self.audio_chunks = []
            self.stop_event.clear()

            self.worker_thread = threading.Thread(
                target=self._record_loop,
                args=(auto_stop_minutes,),
                daemon=True
            )
            self.worker_thread.start()

        auto_str = f" for {auto_stop_minutes} minutes" if auto_stop_minutes > 0 else ""
        return (
            f"[RECORDING] Meeting recording started: '{self.meeting_title}'{auto_str}.\n"
            "Jarvis is now listening to your meeting audio. I will take notes, transcribe, "
            "and summarize when you call stop_meeting_recording()."
        )

    def _record_loop(self, auto_stop_minutes: float):
        max_seconds = auto_stop_minutes * 60.0 if auto_stop_minutes > 0 else 0.0

        try:
            with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32", blocksize=BLOCK_SIZE) as stream:
                while not self.stop_event.is_set():
                    data, overflowed = stream.read(BLOCK_SIZE)
                    self.audio_chunks.append(data[:, 0].copy())

                    if max_seconds > 0 and (time.time() - self.start_time) >= max_seconds:
                        break
        except Exception as e:
            print(f"Error during meeting recording: {e}")
        finally:
            with self.lock:
                self.is_recording = False

    def stop(self, generate_summary: bool = True) -> str:
        with self.lock:
            if not self.is_recording and not self.audio_chunks:
                return "No meeting is currently being recorded."

            self.stop_event.set()
            self.is_recording = False

        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=3)

        if not self.audio_chunks:
            return "No audio was captured during the meeting."

        # Concatenate audio
        audio_data = np.concatenate(self.audio_chunks, axis=0)
        duration_sec = len(audio_data) / SAMPLE_RATE

        timestamp = dt.datetime.now().strftime("%Y-%m-%d_%H%M%S")
        safe_title = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in self.meeting_title)
        wav_filename = f"{timestamp}_{safe_title}.wav"
        wav_path = MEETINGS_DIR / wav_filename

        # Save WAV file
        try:
            scaled_audio = np.int16(audio_data * 32767)
            wavfile.write(str(wav_path), SAMPLE_RATE, scaled_audio)
        except Exception as e:
            print(f"Error writing meeting wav: {e}")

        if not generate_summary:
            return f"Recording saved to {wav_path} ({duration_sec / 60:.1f} minutes). Transcription skipped."

        return process_meeting_audio(wav_path, self.meeting_title, duration_sec)

    def status(self) -> str:
        with self.lock:
            if not self.is_recording:
                return "No meeting recording is currently active."
            elapsed_min = (time.time() - self.start_time) / 60.0
            return f"[RECORDING] Currently recording meeting '{self.meeting_title}' ({elapsed_min:.1f} min elapsed)."


recorder = MeetingRecorder()


# --------------------------------------------------------------------------
# Audio Processing & AI Meeting Notes Generation
# --------------------------------------------------------------------------

def process_meeting_audio(wav_path: Path, title: str, duration_sec: float) -> str:
    """Transcribe audio with faster-whisper and summarize with AI."""
    import jarvis
    import voice

    print(f"Transcribing meeting audio ({duration_sec / 60:.1f} min)...")
    
    # 1. Transcribe with Whisper
    try:
        if voice._whisper is None:
            from faster_whisper import WhisperModel
            size = os.getenv("JARVIS_WHISPER_MODEL", "small")
            voice._whisper = WhisperModel(size, device="cpu", compute_type="int8")

        segments, info = voice._whisper.transcribe(
            str(wav_path),
            beam_size=5,
            vad_filter=True,
            language="en"
        )

        transcript_lines = []
        for s in segments:
            start_m, start_s = divmod(int(s.start), 60)
            end_m, end_s = divmod(int(s.end), 60)
            text = s.text.strip()
            if text:
                transcript_lines.append(f"[{start_m:02d}:{start_s:02d} - {end_m:02d}:{end_s:02d}] {text}")

        full_transcript = "\n".join(transcript_lines)
    except Exception as e:
        return f"Audio saved to {wav_path.name}, but transcription failed: {e}"

    if not full_transcript.strip():
        return f"Audio saved to {wav_path.name}, but no intelligible speech was detected."

    # 2. Generate Structured Meeting Minutes with LLM
    prompt = (
        f"You are Jarvis, an executive meeting assistant. Below is the transcript of a meeting titled '{title}'.\n"
        "Please generate a comprehensive, highly organized Meeting Summary in Markdown with:\n"
        "1. Executive Summary (2-3 concise paragraphs)\n"
        "2. Key Topics & Discussion Points (bullet points with details)\n"
        "3. Decisions Made (explicit agreements reached)\n"
        "4. Action Items & Next Steps (format: - [ ] Task name | Owner | Due Date YYYY-MM-DD if mentioned)\n\n"
        f"Meeting Transcript:\n{full_transcript[:12000]}"
    )

    try:
        res = jarvis.client.chat.completions.create(
            model=jarvis.MODEL,
            messages=[
                {"role": "system", "content": "You are an expert executive meeting summarizer."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500
        )
        summary_markdown = res.choices[0].message.content or "Summary generation returned empty."
    except Exception as e:
        summary_markdown = f"Transcript captured successfully, but AI summary failed: {e}\n\nFull Transcript:\n{full_transcript}"

    # 3. Save Markdown Meeting Notes
    now = dt.datetime.now()
    note_filename = f"meeting_notes_{now:%Y-%m-%d_%H%M}.md"
    note_path = NOTES_DIR / note_filename

    note_content = (
        f"# 📋 Meeting Notes: {title}\n"
        f"**Date:** {now:%A, %d %B %Y, %H:%M}\n"
        f"**Duration:** {duration_sec / 60:.1f} minutes\n"
        f"**Audio Recording:** `{wav_path.name}`\n\n"
        "## Meeting Minutes & Summary\n\n"
        f"{summary_markdown}\n\n"
        "---\n\n"
        "## Full Timestamped Transcript\n\n"
        f"{full_transcript}\n"
    )

    try:
        note_path.write_text(note_content, encoding="utf-8")
    except Exception as e:
        print(f"Failed to write note file: {e}")

    # 4. Auto-detect action items and add to task table
    tasks_added = []
    for line in summary_markdown.splitlines():
        if line.strip().startswith("- [ ]") or "Action Item" in line:
            task_title = line.replace("- [ ]", "").replace("*", "").strip()
            if len(task_title) > 5 and not task_title.startswith("#"):
                try:
                    jarvis.add_task(f"[{title}] {task_title[:80]}")
                    tasks_added.append(task_title[:80])
                except Exception:
                    pass

    tasks_notice = f"\n\n* Added {len(tasks_added)} action item(s) to your tasks list." if tasks_added else ""

    return (
        f"**Meeting Notes Generated for '{title}'**\n"
        f"Saved to: `notes/{note_filename}`\n"
        f"Duration: {duration_sec / 60:.1f} min\n\n"
        f"{summary_markdown}{tasks_notice}"
    )


# --------------------------------------------------------------------------
# Tool Wrappers
# --------------------------------------------------------------------------

def start_meeting_recording(title: str = "Meeting", auto_stop_minutes: float = 0.0) -> str:
    """
    Start listening to and recording a live meeting, lecture, or call in the background.
    Will record continuously until stop_meeting_recording is called, or auto-stop after specified minutes.
    """
    return recorder.start(title=title, auto_stop_minutes=auto_stop_minutes)


def stop_meeting_recording(generate_summary: bool = True) -> str:
    """
    Stop the current meeting recording, transcribe the audio using Whisper AI,
    generate structured meeting notes with executive summary, decisions, and action items,
    and save to the notes folder.
    """
    return recorder.stop(generate_summary=generate_summary)


def record_meeting(duration_minutes: float = 5.0, title: str = "Meeting") -> str:
    """
    Listen to and record a meeting for a specific duration in minutes, then automatically
    transcribe it, take structured notes, and extract action items.
    """
    if duration_minutes <= 0 or duration_minutes > 180:
        return "Duration must be between 1 and 180 minutes."

    recorder.start(title=title, auto_stop_minutes=duration_minutes)
    return (
        f"[RECORDING] Jarvis is now listening to and recording '{title}' for {duration_minutes} minutes.\n"
        "You can continue using your laptop. When the time is up (or when you call stop_meeting_recording), "
        "I will transcribe the entire meeting, generate detailed notes, and extract all action items for you."
    )


def get_meeting_status() -> str:
    """Check if Jarvis is currently recording a live meeting or call."""
    return recorder.status()


# --------------------------------------------------------------------------
# Registry & Schemas
# --------------------------------------------------------------------------

REGISTRY = {
    "start_meeting_recording": (start_meeting_recording, False),
    "stop_meeting_recording": (stop_meeting_recording, False),
    "record_meeting": (record_meeting, False),
    "get_meeting_status": (get_meeting_status, False),
}

SCHEMAS = [
    {
        "name": "start_meeting_recording",
        "description": (
            "Start listening to and recording a live meeting, Zoom/Meet/Teams call, lecture, or discussion. "
            "Runs in the background and captures audio until stopped."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Title or topic of the meeting, e.g. 'Product Sync'"},
                "auto_stop_minutes": {
                    "type": "number",
                    "description": "Optional: number of minutes to automatically stop recording (e.g. 30.0). Defaults to 0 (manual stop)."
                }
            }
        }
    },
    {
        "name": "stop_meeting_recording",
        "description": (
            "Stop active meeting recording, transcribe with Whisper AI, generate executive summary, "
            "decisions, and action items, and save the notes to notes/."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "generate_summary": {
                    "type": "boolean",
                    "description": "Whether to generate AI summary and extract action items. Defaults to true."
                }
            }
        }
    },
    {
        "name": "record_meeting",
        "description": (
            "Record a meeting or lecture for a given duration (e.g. 15, 30, 45 minutes), "
            "then transcribe, generate structured notes, and save."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "duration_minutes": {"type": "number", "description": "Duration to record in minutes (e.g. 10.0)"},
                "title": {"type": "string", "description": "Title or topic of the meeting"}
            },
            "required": ["duration_minutes"]
        }
    },
    {
        "name": "get_meeting_status",
        "description": "Check if a meeting recording is currently in progress and how many minutes have elapsed.",
        "input_schema": {"type": "object", "properties": {}}
    }
]
