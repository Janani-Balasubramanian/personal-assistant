"""
WhatsApp Persona & Intelligent Messaging Suite for Jarvis.
Allows Jarvis to draft replies that sound authentically like you, manage your
contacts and relationships, and dispatch WhatsApp messages directly on Windows.
"""

import json
import os
import re
import sys
import time
import urllib.parse
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PERSONA_FILE = BASE_DIR / "whatsapp_persona.json"


def _load_persona() -> dict:
    if not PERSONA_FILE.exists():
        return {
            "user_name": "Janani",
            "tone": "Warm, concise, friendly, casual with friends, polite with elders.",
            "habits": ["Keep replies short (1-2 sentences)", "Sound natural, never robotic"],
            "contacts": {},
        }
    try:
        with open(PERSONA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"user_name": "Janani", "tone": "Friendly and concise", "habits": [], "contacts": {}}


def _save_persona(data: dict) -> None:
    try:
        with open(PERSONA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving persona: {e}")


def save_whatsapp_contact(name: str, phone: str, relationship: str = "friend", tone_note: str = "") -> str:
    """Save or update a WhatsApp contact with their phone number, relationship, and custom tone notes."""
    clean_name = name.strip().lower()
    clean_phone = re.sub(r"[^\d+]", "", phone.strip())
    if not clean_phone:
        return "Please provide a valid phone number (e.g. +919876543210 or 9876543210)."

    # Auto prefix India country code if 10 digits
    if len(clean_phone) == 10 and not clean_phone.startswith("+"):
        clean_phone = "+91" + clean_phone

    data = _load_persona()
    data["contacts"][clean_name] = {
        "display_name": name.strip(),
        "phone": clean_phone,
        "relationship": relationship.strip().lower(),
        "tone_note": tone_note.strip() or f"Treat as {relationship}",
    }
    _save_persona(data)
    return f"Saved WhatsApp contact: '{name.strip()}' -> {clean_phone} ({relationship})."


def list_whatsapp_contacts() -> str:
    """List all saved WhatsApp contacts, numbers, and relationship tones."""
    data = _load_persona()
    contacts = data.get("contacts", {})
    if not contacts:
        return "No WhatsApp contacts saved yet. Use save_whatsapp_contact(name, phone, relationship) to add contacts."

    lines = ["Saved WhatsApp Contacts:"]
    for k, v in contacts.items():
        rel = v.get("relationship", "contact")
        ph = v.get("phone", "N/A")
        note = v.get("tone_note", "")
        lines.append(f"- {v.get('display_name', k)} ({rel}): {ph} [Tone: {note}]")
    return "\n".join(lines)


def draft_reply_in_my_voice(contact: str, incoming_message: str) -> str:
    """
    Draft a WhatsApp reply to an incoming message mimicking your personal tone,
    relationship rules, and texting habits.
    """
    data = _load_persona()
    user_name = data.get("user_name", "Janani")
    tone_desc = data.get("tone", "Friendly, warm, and concise.")
    habits = "\n".join(f"- {h}" for h in data.get("habits", []))

    contact_key = contact.strip().lower()
    contact_info = data.get("contacts", {}).get(contact_key, {})
    rel = contact_info.get("relationship", "friend or acquaintance")
    tone_note = contact_info.get("tone_note", f"Casual and polite")

    prompt = (
        f"You are writing a WhatsApp reply on behalf of {user_name}.\n"
        f"Your general communication style:\n{tone_desc}\n\n"
        f"Your texting habits:\n{habits}\n\n"
        f"Recipient: '{contact}' (Relationship: {rel})\n"
        f"Special guidance for this person: {tone_note}\n\n"
        f"Incoming message from {contact}:\n\"{incoming_message}\"\n\n"
        f"Task: Write the exact response {user_name} would send. Output ONLY the response text itself, "
        f"with no quotes, explanations, or robotic intros. Keep it authentic, human, and brief."
    )

    try:
        import jarvis
        client = jarvis.client
        model = jarvis.MODEL

        res = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a personal ghostwriter. Output only the realistic texting response."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=200,
        )
        reply = res.choices[0].message.content.strip().strip('"').strip("'")
        
        # Copy to clipboard for convenience
        try:
            import pyperclip
            pyperclip.copy(reply)
            clip_note = "\n\n(Draft copied to clipboard - press Ctrl+V to paste into WhatsApp)"
        except Exception:
            clip_note = ""

        return f"Suggested reply for {contact}:\n\"{reply}\"{clip_note}"
    except Exception as e:
        return f"Failed to generate draft: {e}"


def send_whatsapp_message(target: str, message: str, auto_send: bool = False) -> str:
    """
    Open WhatsApp to the contact's chat with the message pre-filled.
    Target can be a contact name (e.g. 'mom', 'rahul') or a phone number.
    If auto_send is True, sends automatically after opening.
    """
    clean_target = target.strip()
    data = _load_persona()
    contacts = data.get("contacts", {})

    phone = None
    target_lower = clean_target.lower()
    if target_lower in contacts:
        phone = contacts[target_lower].get("phone")
    elif re.sub(r"[^\d+]", "", clean_target):
        phone = re.sub(r"[^\d+]", "", clean_target)
        if len(phone) == 10 and not phone.startswith("+"):
            phone = "+91" + phone

    if not phone:
        return (
            f"Contact '{target}' not found in saved WhatsApp contacts. "
            "Please provide their phone number or save them with `save_whatsapp_contact`."
        )

    # Clean phone (digits only for whatsapp URL)
    phone_digits = re.sub(r"[^\d]", "", phone)
    encoded_msg = urllib.parse.quote(message.strip())

    # Try WhatsApp Desktop Protocol first, fallback to WhatsApp Web
    desktop_url = f"whatsapp://send?phone={phone_digits}&text={encoded_msg}"
    web_url = f"https://web.whatsapp.com/send?phone={phone_digits}&text={encoded_msg}"

    opened = False
    if sys.platform == "win32":
        try:
            os.startfile(desktop_url)
            opened = True
        except Exception:
            pass

    if not opened:
        import webbrowser
        webbrowser.open(web_url)

    if auto_send:
        # Wait for WhatsApp window to gain focus, then send
        time.sleep(2.5)
        try:
            import pyautogui
            pyautogui.press("enter")
            return f"WhatsApp message sent to {target} ({phone}): '{message}'"
        except Exception as e:
            return f"WhatsApp opened for {target}, but auto-press Enter failed: {e}. You can press Enter manually."

    return f"WhatsApp opened for {target} ({phone}) with your message ready to review and send."


def update_my_texting_style(new_tone: str, new_rules: str = "") -> str:
    """Update your personal texting style and habits so Jarvis mimics you even better."""
    data = _load_persona()
    if new_tone:
        data["tone"] = new_tone.strip()
    if new_rules:
        rules_list = [r.strip() for r in new_rules.split(",") if r.strip()]
        data["habits"].extend(rules_list)
        # Deduplicate
        data["habits"] = list(dict.fromkeys(data["habits"]))

    _save_persona(data)
    return "Your WhatsApp texting style profile has been updated successfully!"


REGISTRY = {
    "save_whatsapp_contact": (save_whatsapp_contact, False),
    "list_whatsapp_contacts": (list_whatsapp_contacts, False),
    "draft_reply_in_my_voice": (draft_reply_in_my_voice, False),
    "send_whatsapp_message": (send_whatsapp_message, True),  # Requires user confirmation for safety
    "update_my_texting_style": (update_my_texting_style, False),
}

SCHEMAS = [
    {
        "name": "save_whatsapp_contact",
        "description": "Save or update a WhatsApp contact's name, phone number, relationship (friend, family, work), and custom tone notes.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Contact name (e.g. 'Mom', 'Priya', 'Boss')"},
                "phone": {"type": "string", "description": "Phone number with country code (e.g. '+919876543210')"},
                "relationship": {"type": "string", "description": "Relationship: 'family', 'friend', 'work', 'client', etc."},
                "tone_note": {"type": "string", "description": "Optional notes on how to speak to them (e.g. 'very casual, funny', 'strictly professional')"},
            },
            "required": ["name", "phone"],
        },
    },
    {
        "name": "list_whatsapp_contacts",
        "description": "List all saved WhatsApp contacts, phone numbers, and relationship profiles.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "draft_reply_in_my_voice",
        "description": "Draft a personalized WhatsApp reply to an incoming message from a contact, mimicking your personal tone, relationship rules, and texting habits.",
        "input_schema": {
            "type": "object",
            "properties": {
                "contact": {"type": "string", "description": "Name of the person who sent the message"},
                "incoming_message": {"type": "string", "description": "The message they sent you"},
            },
            "required": ["contact", "incoming_message"],
        },
    },
    {
        "name": "send_whatsapp_message",
        "description": "Send a WhatsApp message to a contact or phone number. Requires confirmation before dispatching.",
        "input_schema": {
            "type": "object",
            "properties": {
                "target": {"type": "string", "description": "Contact name (e.g. 'mom', 'priya') or phone number"},
                "message": {"type": "string", "description": "Message text to send"},
                "auto_send": {"type": "boolean", "description": "Whether to automatically press enter to send (default false)"},
            },
            "required": ["target", "message"],
        },
    },
    {
        "name": "update_my_texting_style",
        "description": "Teach Jarvis how you text: update your tone description and list of personal habits/rules.",
        "input_schema": {
            "type": "object",
            "properties": {
                "new_tone": {"type": "string", "description": "Description of how you talk/text"},
                "new_rules": {"type": "string", "description": "Comma-separated rules (e.g. 'use emojis, keep replies short')"},
            },
        },
    },
]

