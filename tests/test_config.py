"""
Tests — Configuration
"""

import os

from config import Settings, LLMConfig, AudioConfig, AgentConfig


class TestConfig:
    def test_defaults(self):
        s = Settings()
        assert s.llm.text_model == os.getenv("OLLAMA_TEXT_MODEL", "llama3.2")
        assert s.audio.sample_rate == 16_000
        assert s.agent.confirm_destructive is True
        assert s.debug in (True, False)

    def test_llm_config(self):
        cfg = LLMConfig()
        assert cfg.host.startswith("http")
        assert cfg.temperature >= 0
        assert cfg.max_tokens > 0

    def test_audio_config(self):
        cfg = AudioConfig()
        assert cfg.stt_language == "en"
        assert cfg.channels == 1
        assert cfg.push_to_talk_key == os.getenv("PTT_KEY", "space")

    def test_agent_config(self):
        cfg = AgentConfig()
        assert cfg.max_memory_turns > 0
        assert cfg.max_screenshot_age_secs > 0
