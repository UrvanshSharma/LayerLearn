"""
Vision Analysis — Precise & Fast
==================================
Multimodal screen understanding with structured output.
Supports both Ollama and Google Gemma API backends.
Defaults to Gemma 4 for superior speed and accuracy.
"""

from __future__ import annotations

import base64
from io import BytesIO

from PIL import Image

from config import settings
from core.logger import get_logger
from core.window_utils import get_front_app_name

log = get_logger(__name__)


def _use_gemma() -> bool:
    """Check if Gemma backend is configured and enabled."""
    return (
        settings.llm.backend.lower() == "gemma"
        and settings.llm.google_api_key
    )


def analyze_image(
    image: Image.Image | str,
    prompt: str = "Describe this screen.",
) -> str:
    """Fast multimodal analysis using Gemma or Ollama."""
    if isinstance(image, str):
        image = Image.open(image)

    log.info("👁  Vision: '{}' …", prompt[:60])

    # Try Gemma first if configured
    if _use_gemma():
        try:
            from core.gemma_client import get_gemma_client
            client = get_gemma_client()
            return client.analyze_image(image, prompt)
        except Exception as e:
            log.warning("Gemma vision failed, falling back to Ollama: {}", e)
    
    # Fallback to Ollama
    try:
        import ollama
        from core.screen_capture import capture_full_screen
        
        max_w = settings.agent.screen_max_width
        if image.width > max_w:
            ratio = max_w / image.width
            image = image.resize((max_w, int(image.height * ratio)), Image.LANCZOS)

        buf = BytesIO()
        image.save(buf, format="JPEG", quality=settings.agent.screen_capture_quality)
        b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

        response = ollama.chat(
            model=settings.llm.vision_model,
            messages=[{
                "role": "user",
                "content": prompt,
                "images": [b64],
            }],
            options={
                "temperature": 0.2,
                "num_predict": 512,
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
    active_app = get_front_app_name() or "Unknown"

    if prompt is None:
        prompt = f"""You are looking at a desktop screen. The active/frontmost app is: {active_app}

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
    active_app = get_front_app_name() or "Unknown"

    prompt = f"""You are looking at a desktop screen. Active app: {active_app}

The user asks: "{question}"

Look at the screen carefully and give a DIRECT, PRECISE answer.
If you can read text on screen, quote it exactly.
Do NOT guess — describe only what you can see."""

    return analyze_image(img, prompt)


def analyze_code_on_screen(instruction: str = "Help me with this code") -> str:
    """Capture screen → understand code → give guidance."""
    from core.screen_capture import capture_full_screen

    img, path = capture_full_screen()
    active_app = get_front_app_name() or "Unknown"

    prompt = f"""You are looking at code on a desktop screen. Active app: {active_app}
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
