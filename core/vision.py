"""
Vision Analysis — Precise & Fast
==================================
Multimodal screen understanding with structured output.
The prompts are designed to force the LLM to give PRECISE, USEFUL descriptions.
"""

from __future__ import annotations

import base64
import subprocess
from io import BytesIO
from typing import Optional

import ollama
from PIL import Image

from config import settings
from core.logger import get_logger

log = get_logger(__name__)


def _image_to_base64(img: Image.Image) -> str:
    """Downscale + compress image for fast inference."""
    max_w = settings.agent.screen_max_width
    if img.width > max_w:
        ratio = max_w / img.width
        img = img.resize((max_w, int(img.height * ratio)), Image.LANCZOS)

    buf = BytesIO()
    img.save(buf, format="JPEG", quality=settings.agent.screen_capture_quality)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def _get_active_app() -> str:
    """Get the currently active app name for context."""
    try:
        script = 'tell application "System Events" to name of first application process whose frontmost is true'
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=1,
        )
        return result.stdout.strip()
    except Exception:
        return "Unknown"


def analyze_image(
    image: Image.Image | str,
    prompt: str = "Describe this screen.",
) -> str:
    """Fast multimodal analysis."""
    if isinstance(image, str):
        image = Image.open(image)

    b64 = _image_to_base64(image)
    log.info("👁  Vision: '{}' …", prompt[:60])

    try:
        response = ollama.chat(
            model=settings.llm.vision_model,
            messages=[{
                "role": "user",
                "content": prompt,
                "images": [b64],
            }],
            options={
                "temperature": 0.2,  # low temp for precise descriptions
                "num_predict": 512,  # keep it concise
            },
            keep_alive=settings.llm.keep_alive,
        )
        result = response["message"]["content"]
        log.debug("Vision result ({} chars)", len(result))
        return result
    except Exception as e:
        log.error("Vision failed: {}", e)
        return f"[Vision error: {e}]"


def analyze_screen(prompt: str | None = None) -> str:
    """Capture screen + analyze with context about active app."""
    from core.screen_capture import capture_full_screen
    img, path = capture_full_screen()

    active_app = _get_active_app()

    if prompt is None:
        prompt = f"""You are looking at a Mac screen. The active/frontmost app is: {active_app}

Describe EXACTLY what you see. Be SPECIFIC and PRECISE:
1. What app is in the foreground? What is its current state?
2. What text/content is visible? Read important text literally.
3. Are there any errors, warnings, or notifications?
4. What tabs, windows, or panels are open?
5. What buttons or interactive elements are visible?

Be direct and factual. Don't say "it appears" — say what IS there."""
    return analyze_image(img, prompt)


def analyze_screen_with_question(question: str) -> str:
    """Capture screen + answer a specific question."""
    from core.screen_capture import capture_full_screen
    img, path = capture_full_screen()

    active_app = _get_active_app()

    prompt = f"""You are looking at a Mac screen. Active app: {active_app}

The user asks: "{question}"

Look at the screen carefully and give a DIRECT, PRECISE answer.
If you can read text on screen, quote it exactly.
Do NOT guess — describe only what you can see."""

    return analyze_image(img, prompt)


def analyze_code_on_screen(instruction: str = "Help me with this code") -> str:
    """Capture screen → understand code → give guidance."""
    from core.screen_capture import capture_full_screen
    img, path = capture_full_screen()

    active_app = _get_active_app()

    prompt = f"""You are looking at code on a Mac screen. Active app: {active_app}
The user says: "{instruction}"

1. READ the code carefully — identify the language. Quote relevant lines.
2. If there are errors/warnings, read them EXACTLY as shown.
3. Explain what's wrong in plain language.
4. Give a SPECIFIC fix with corrected code.

Be precise — quote actual code and error messages from the screen."""

    return analyze_image(img, prompt)


def generate_code_from_screen(instruction: str) -> str:
    """Capture screen → generate code fix/patch."""
    from core.screen_capture import capture_full_screen
    img, path = capture_full_screen()

    prompt = f"""Look at the code on screen. The user says: "{instruction}"

Generate ONLY the corrected code. Show the fix as a clean code block.
Add brief comments on what changed and why."""

    return analyze_image(img, prompt)


def read_screen_text() -> str:
    """Capture screen and extract all visible text."""
    from core.screen_capture import capture_full_screen
    img, path = capture_full_screen()

    prompt = (
        "Read and transcribe ALL visible text on this screen. "
        "Include: window titles, menu items, code, labels, buttons, status bars, URLs. "
        "Preserve the layout. Be complete and exact."
    )
    return analyze_image(img, prompt)
