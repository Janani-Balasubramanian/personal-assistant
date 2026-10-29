"""
Smart Clipboard AI Copilot for Jarvis.
Reads the current text on the Windows clipboard, transforms it using LLM intelligence
(summarize, fix grammar, explain code, translate, or extract key action items),
and copies the result directly back to the clipboard ready for pasting.
"""

import os
import pyperclip


def process_clipboard(action: str = "summarize", custom_instruction: str = "") -> str:
    """Read the current Windows clipboard, apply AI intelligence to it, and copy the enhanced result back to the clipboard."""
    try:
        text = pyperclip.paste()
    except Exception as e:
        return f"Could not read from clipboard: {e}"

    if not text or not text.strip():
        return "Your clipboard is currently empty. Copy some text first (Ctrl+C) and try again."

    # Truncate very long texts to prevent excessive tokens
    sample = text.strip()
    if len(sample) > 8000:
        sample = sample[:8000] + "\n...[truncated for length]"

    action_prompts = {
        "summarize": "Summarize this text clearly in 2-3 concise bullet points:",
        "fix_grammar": "Proofread and polish this text. Fix all grammar, spelling, punctuation and tone errors. Return only the polished version without introductory commentary:",
        "explain": "Explain what this text or code snippet does in clear, simple terms:",
        "extract_tasks": "Extract all action items, deadlines, and tasks mentioned in this text as a checklist:",
        "to_json": "Convert this unstructured data into clean, valid JSON:",
    }

    instruction = custom_instruction.strip() if custom_instruction else action_prompts.get(action.lower().strip(), action_prompts["summarize"])

    try:
        import jarvis
        client = jarvis.client
        model = jarvis.MODEL_NAME

        messages = [
            {
                "role": "system",
                "content": "You are Jarvis's clipboard copilot. Deliver concise, high-value output. Unless asked for explanation, prioritize outputting the clean transformed text ready to be pasted.",
            },
            {
                "role": "user",
                "content": f"{instruction}\n\n---\n{sample}",
            },
        ]

        res = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=800,
        )
        output = res.choices[0].message.content or "No response generated."

        # Write result back to clipboard for instant pasting
        try:
            pyperclip.copy(output)
            copied_note = "(Result copied to your clipboard - press Ctrl+V to paste)"
        except Exception:
            copied_note = ""

        preview = output[:300] + ("..." if len(output) > 300 else "")
        return f"[Clipboard {action.capitalize()}]\n{preview}\n\n{copied_note}"

    except Exception as e:
        return f"Clipboard processing failed: {e}"


REGISTRY = {
    "process_clipboard": (process_clipboard, False),
}

SCHEMAS = [
    {
        "name": "process_clipboard",
        "description": "Read copied text from the Windows clipboard, apply AI transformation (summarize, fix_grammar, explain, extract_tasks, to_json, or custom), and copy the result back to clipboard.",
        "input_schema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["summarize", "fix_grammar", "explain", "extract_tasks", "to_json", "custom"],
                    "description": "The transformation to perform on clipboard text. Defaults to 'summarize'.",
                },
                "custom_instruction": {
                    "type": "string",
                    "description": "Custom prompt or instruction if action is 'custom' or special formatting is requested.",
                },
            },
        },
    },
]

