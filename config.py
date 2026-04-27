"""
LayerLearn Configuration
========================
Tuned for maximum speed + accurate screen reading.
"""

import os
from pathlib import Path
from dataclasses import dataclass, field

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── Paths ────────────────────────────────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parent
ASSETS_DIR = ROOT_DIR / "assets"
LOGS_DIR = ROOT_DIR / "logs"
ASSETS_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)


@dataclass
class LLMConfig:
    """LLM settings (supports both Ollama and Google Gemma)."""
    # Backend selection
    backend: str = os.getenv("LLM_BACKEND", "gemma")  # "gemma" or "ollama"
    
    # Google Gemma API
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
    gemma_model: str = os.getenv("GEMMA_MODEL", "gemini-2.0-flash")  # Latest fast model
    
    # Ollama (fallback)
    host: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    text_model: str = os.getenv("OLLAMA_TEXT_MODEL", "llama3.2")
    vision_model: str = os.getenv("OLLAMA_VISION_MODEL", "llama3.2-vision")
    
    # Shared settings
    temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.3"))
    max_tokens: int = int(os.getenv("LLM_MAX_TOKENS", "512"))  # shorter = faster
    keep_alive: str = "30m"


@dataclass
class AudioConfig:
    """Voice pipeline settings."""
    stt_model_size: str = os.getenv("STT_MODEL_SIZE", "small")
    stt_language: str = os.getenv("STT_LANGUAGE", "en")
    tts_voice: str = os.getenv("TTS_VOICE", "en-US-AriaNeural")
    tts_rate: str = os.getenv("TTS_RATE", "+20%")  # faster speech for snappier feel
    sample_rate: int = 16_000
    channels: int = 1
    push_to_talk_key: str = os.getenv("PTT_KEY", "shift")


@dataclass
class AgentConfig:
    """Agent behaviour settings."""
    max_memory_turns: int = int(os.getenv("MAX_MEMORY_TURNS", "20"))
    max_screenshot_age_secs: int = 120
    confirm_destructive: bool = True
    screen_capture_quality: int = 70  # higher quality = better text reading
    screen_max_width: int = 1280     # bigger = vision model reads text better


@dataclass
class Settings:
    llm: LLMConfig = field(default_factory=LLMConfig)
    audio: AudioConfig = field(default_factory=AudioConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"


settings = Settings()
