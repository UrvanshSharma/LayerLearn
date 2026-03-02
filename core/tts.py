"""
Text-to-Speech (TTS)
====================
Streaming TTS using edge-tts (free Microsoft Azure voices).
Audio is played back in real-time via sounddevice.
"""

from __future__ import annotations

import asyncio

import edge_tts
import sounddevice as sd
import numpy as np

from config import settings
from core.logger import get_logger

log = get_logger(__name__)


async def speak(text: str, stop_event=None) -> None:
    """
    Stream TTS audio for *text* to the default speaker.
    If *stop_event* (threading.Event) is set mid-playback, stops immediately.
    """
    if not text.strip():
        return

    # Strip markdown / code blocks for cleaner speech
    clean_text = _clean_for_speech(text)
    if not clean_text.strip():
        return

    log.info("TTS speaking: '{}' …", clean_text[:80])

    try:
        communicate = edge_tts.Communicate(
            clean_text,
            voice=settings.audio.tts_voice,
            rate=settings.audio.tts_rate,
        )

        # Collect audio data
        audio_data = bytearray()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data.extend(chunk["data"])
            if stop_event and stop_event.is_set():
                log.debug("TTS interrupted during streaming")
                return

        if not audio_data:
            log.warning("TTS produced no audio data")
            return

        # Decode MP3 → raw samples with pydub
        samples, sr = _decode_mp3(bytes(audio_data))
        if samples is None:
            return

        # Play audio (blocking, in executor to not block async loop)
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, _play_blocking, samples, sr, stop_event)

    except asyncio.CancelledError:
        log.debug("TTS task cancelled")
        raise
    except Exception as e:
        log.error("TTS failed: {}", e)


def _decode_mp3(data: bytes):
    """Decode MP3 bytes to float32 numpy array using pydub."""
    try:
        from pydub import AudioSegment
        import io

        audio = AudioSegment.from_file(io.BytesIO(data), format="mp3")
        audio = audio.set_frame_rate(24000).set_channels(1).set_sample_width(2)
        samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
        samples = samples / 32768.0  # normalize to [-1, 1]
        return samples, 24000
    except Exception as e:
        log.error("Failed to decode MP3 audio: {}", e)
        return None, None


def _play_blocking(samples: np.ndarray, sr: int, stop_event=None) -> None:
    """Play samples via sounddevice with cooperative interruption."""
    if stop_event and stop_event.is_set():
        return

    try:
        sd.play(samples, samplerate=sr, blocking=False)

        total_ms = int((len(samples) / sr) * 1000)
        elapsed_ms = 0
        poll_ms = 40

        while elapsed_ms < total_ms:
            if stop_event and stop_event.is_set():
                sd.stop()
                log.debug("TTS playback interrupted")
                return
            sd.sleep(poll_ms)
            elapsed_ms += poll_ms

        sd.wait()
        log.debug("TTS playback complete ({:.1f}s)", len(samples) / sr)
    except Exception as e:
        log.error("Audio playback failed: {}", e)


def _clean_for_speech(text: str) -> str:
    """Remove markdown formatting, code blocks, etc. for cleaner TTS."""
    import re
    # Remove code blocks
    text = re.sub(r"```[\s\S]*?```", " (code block omitted) ", text)
    # Remove inline code
    text = re.sub(r"`([^`]+)`", r"\1", text)
    # Remove markdown headers
    text = re.sub(r"#{1,6}\s*", "", text)
    # Remove bold/italic markers
    text = re.sub(r"\*{1,3}([^*]+)\*{1,3}", r"\1", text)
    # Remove bullet points
    text = re.sub(r"^\s*[-*]\s+", "", text, flags=re.MULTILINE)
    # Collapse whitespace
    text = re.sub(r"\n{2,}", ". ", text)
    text = re.sub(r"\n", " ", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


def speak_sync(text: str, stop_event=None) -> None:
    """Synchronous wrapper for speak()."""
    try:
        loop = asyncio.get_running_loop()
        # If we're already in an async context, schedule it
        asyncio.ensure_future(speak(text, stop_event))
    except RuntimeError:
        asyncio.run(speak(text, stop_event))
