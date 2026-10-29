"""
Screen vision tools for Jarvis.
Allows Jarvis to 'see' the user's desktop screen, analyze errors, read documents,
and answer visual questions using multimodal AI vision.
"""

import base64
import io
import os
from pathlib import Path


def _capture_screen_base64() -> str:
    """Capture the screen and return as a compact base64 JPEG."""
    from PIL import ImageGrab
    img = ImageGrab.grab()
    
    # Scale down if very high resolution to keep latency low
    max_dim = 1280
    if img.width > max_dim or img.height > max_dim:
        img.thumbnail((max_dim, max_dim))
    
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=80)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def see_screen(question: str = "Explain what is on the screen and any active errors or open windows.") -> str:
    """Take a screenshot of the primary screen and analyze it with visual AI."""
    try:
        b64_img = _capture_screen_base64()
    except Exception as e:
        return f"Unable to capture screen: {e} (make sure Jarvis is running in your active desktop session)."

    try:
        import jarvis
        client = jarvis.client
        
        # Use a vision-capable Gemini model
        model = os.getenv("JARVIS_VISION_MODEL", "gemini-2.5-flash")
        
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"You are Jarvis looking at the user's desktop screen. {question}. Be concise and practical."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}}
                ]
            }
        ]

        res = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=500
        )
        return res.choices[0].message.content or "No visual details detected."
    except Exception as e:
        return f"Vision analysis failed: {e}"


def save_screenshot(filename: str = "screenshot.png") -> str:
    """Capture and save a screenshot of the screen to disk."""
    try:
        from PIL import ImageGrab
        img = ImageGrab.grab()
        path = Path(filename).resolve()
        img.save(str(path))
        return f"Screenshot saved to: {path}"
    except Exception as e:
        return f"Failed to save screenshot: {e}"


REGISTRY = {
    "see_screen": (see_screen, False),
    "save_screenshot": (save_screenshot, False),
}

SCHEMAS = [
    {
        "name": "see_screen",
        "description": "Capture the user's computer screen and visually inspect it to read errors, explain code, diagnose UI bugs, or summarize open pages.",
        "input_schema": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "What to look for on screen, e.g. 'What error is shown in the terminal?'"
                }
            },
        },
    },
    {
        "name": "save_screenshot",
        "description": "Capture the desktop screen and save the image to a file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "Output filename, e.g. 'desktop_capture.png'"}
            },
        },
    },
]
