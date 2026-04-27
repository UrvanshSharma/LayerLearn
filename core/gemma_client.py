"""
Gemma 4 / Google Generative AI Client
======================================
High-performance LLM backend using Google's Gemini API (includes Gemma models).
Provides fast, accurate responses for both text and vision tasks.
"""

from __future__ import annotations

import base64
from io import BytesIO
from typing import Optional

import google.generativeai as genai
from PIL import Image

from config import settings
from core.logger import get_logger

log = get_logger(__name__)


class GemmaClient:
    """Wrapper for Google Generative AI (Gemini/Gemma) API."""

    def __init__(self):
        """Initialize Gemma client with API key."""
        if not settings.llm.google_api_key:
            raise ValueError(
                "GOOGLE_API_KEY not set in .env. "
                "Get a free API key at https://makersuite.google.com/app/apikey"
            )
        
        genai.configure(api_key=settings.llm.google_api_key)
        self.model_name = settings.llm.gemma_model
        log.info("✅ Gemma client initialized: {}", self.model_name)

    def _get_model(self):
        """Get the Gemini/Gemma model instance."""
        return genai.GenerativeModel(
            self.model_name,
            generation_config={
                "temperature": settings.llm.temperature,
                "max_output_tokens": settings.llm.max_tokens,
            }
        )

    def generate_text(self, prompt: str) -> str:
        """
        Generate text response for a prompt.
        
        Args:
            prompt: Text prompt
            
        Returns:
            Generated response text
        """
        try:
            model = self._get_model()
            response = model.generate_content(prompt)
            result = response.text
            log.debug("📝 Gemma text: {} chars", len(result))
            return result
        except Exception as e:
            log.error("❌ Gemma text generation failed: {}", e)
            raise

    def analyze_image(
        self,
        image: Image.Image | str,
        prompt: str = "Describe this image.",
    ) -> str:
        """
        Analyze an image with vision capabilities.
        
        Args:
            image: PIL Image or file path
            prompt: Question or instruction for the image
            
        Returns:
            Analysis result
        """
        if isinstance(image, str):
            image = Image.open(image)

        # Downscale for faster processing
        max_w = settings.agent.screen_max_width
        if image.width > max_w:
            ratio = max_w / image.width
            image = image.resize((max_w, int(image.height * ratio)), Image.LANCZOS)

        log.info("👁  Gemma vision: '{}' …", prompt[:60])

        try:
            model = self._get_model()
            response = model.generate_content([prompt, image])
            result = response.text
            log.debug("Vision result ({} chars)", len(result))
            return result
        except Exception as e:
            log.error("❌ Vision analysis failed: {}", e)
            raise

    def analyze_screen(self, prompt: str | None = None) -> str:
        """
        Capture and analyze the screen.
        
        Args:
            prompt: Custom question about the screen
            
        Returns:
            Screen analysis
        """
        from core.screen_capture import capture_full_screen
        from core.window_utils import get_front_app_name
        
        img, path = capture_full_screen()
        active_app = get_front_app_name() or "Unknown"

        if prompt is None:
            prompt = f"""You are looking at a desktop screen. Active app: {active_app}

Describe EXACTLY what you see. Be SPECIFIC and PRECISE:
1. What app is in the foreground? What is its current state?
2. What text/content is visible? Read important text literally.
3. Are there any errors, warnings, or notifications?
4. What tabs, windows, or panels are open?
5. What buttons or interactive elements are visible?

Be direct and factual. Don't say "it appears" — say what IS there."""

        return self.analyze_image(img, prompt)

    def analyze_screen_with_question(self, question: str) -> str:
        """
        Capture screen and answer a specific question.
        
        Args:
            question: User's question about the screen
            
        Returns:
            Answer based on screen content
        """
        from core.screen_capture import capture_full_screen
        from core.window_utils import get_front_app_name
        
        img, path = capture_full_screen()
        active_app = get_front_app_name() or "Unknown"

        prompt = f"""You are looking at a desktop screen. Active app: {active_app}

The user asks: "{question}"

Look at the screen carefully and give a DIRECT, PRECISE answer.
If you can read text on screen, quote it exactly.
Do NOT guess — describe only what you can see."""

        return self.analyze_image(img, prompt)

    def analyze_code_on_screen(self, instruction: str = "Help me with this code") -> str:
        """
        Analyze code visible on screen.
        
        Args:
            instruction: What the user needs help with
            
        Returns:
            Code analysis and guidance
        """
        from core.screen_capture import capture_full_screen
        from core.window_utils import get_front_app_name
        
        img, path = capture_full_screen()
        active_app = get_front_app_name() or "Unknown"

        prompt = f"""You are looking at code on a desktop screen. Active app: {active_app}
The user says: "{instruction}"

1. READ the code carefully — identify the language. Quote relevant lines.
2. If there are errors/warnings, read them EXACTLY as shown.
3. Explain what's wrong in plain language.
4. Give a SPECIFIC fix with corrected code.

Be precise — quote actual code and error messages from the screen."""

        return self.analyze_image(img, prompt)

    def generate_code_from_screen(self, instruction: str) -> str:
        """
        Generate code based on screen content.
        
        Args:
            instruction: What code to generate/fix
            
        Returns:
            Generated code
        """
        from core.screen_capture import capture_full_screen
        
        img, path = capture_full_screen()

        prompt = f"""Look at the code on screen. The user says: "{instruction}"

Generate ONLY the corrected code. Show the fix as a clean code block.
Add brief comments on what changed and why."""

        return self.analyze_image(img, prompt)

    def read_screen_text(self) -> str:
        """
        Extract all visible text from screen.
        
        Returns:
            Complete text transcription
        """
        from core.screen_capture import capture_full_screen
        
        img, path = capture_full_screen()

        prompt = (
            "Read and transcribe ALL visible text on this screen. "
            "Include: window titles, menu items, code, labels, buttons, status bars, URLs. "
            "Preserve the layout. Be complete and exact."
        )
        return self.analyze_image(img, prompt)


# Singleton instance
_gemma_client: Optional[GemmaClient] = None


def get_gemma_client() -> GemmaClient:
    """Get or create the Gemma client singleton."""
    global _gemma_client
    if _gemma_client is None:
        _gemma_client = GemmaClient()
    return _gemma_client
