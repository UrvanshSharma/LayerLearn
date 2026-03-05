"""
Speech-to-Text (STT)
====================
Local streaming transcription using faster-whisper.
Supports push-to-talk recording via sounddevice.
"""

from __future__ import annotations

import queue
import tempfile
import wave
import os
from pathlib import Path

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

from config import settings
from core.logger import get_logger

log = get_logger(__name__)

# ── Lazy-loaded model singleton ──────────────────────────────────────────
_model: WhisperModel | None = None


def _get_model() -> WhisperModel:
    global _model
    if _model is None:
        log.info("Loading Whisper model '{}' …", settings.audio.stt_model_size)

        _model = WhisperModel(
            settings.audio.stt_model_size,
            device="cpu",
            compute_type="int8",
            cpu_threads=6
        )

        log.info("Whisper model loaded ✓")

    return _model


# ─────────────────────────────────────────────────────────────────────────

def record_audio_push_to_talk(stop_event) -> np.ndarray:
    """
    Record audio from the default microphone until *stop_event* is set.
    Returns a 1-D float32 numpy array (16 kHz mono).
    """

    sr = settings.audio.sample_rate
    audio_queue: queue.Queue[np.ndarray] = queue.Queue()

    def _callback(indata, frames, time_info, status):
        if status:
            log.warning("Audio input status: {}", status)

        audio_queue.put(indata.copy())

    with sd.InputStream(
        samplerate=sr,
        channels=1,
        dtype="float32",
        callback=_callback,
    ):
        log.debug("🎙 Recording … (release key to stop)")

        while not stop_event.is_set():
            sd.sleep(50)

    chunks: list[np.ndarray] = []

    while not audio_queue.empty():
        chunks.append(audio_queue.get())

    if not chunks:
        return np.array([], dtype="float32")

    return np.concatenate(chunks, axis=0).flatten()


# ─────────────────────────────────────────────────────────────────────────

def transcribe(audio: np.ndarray) -> str:
    """
    Transcribe a numpy audio array to text.
    Returns the full transcription string.
    """

    if audio.size == 0:
        return ""

    model = _get_model()

    # Create temp file path (closed immediately → no Windows lock)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        wav_path = tmp.name

    try:
        _write_wav(wav_path, audio, settings.audio.sample_rate)

        segments, info = model.transcribe(
            wav_path,
            language=settings.audio.stt_language,
            beam_size=5,
            vad_filter=True,
        )

        text = " ".join(seg.text.strip() for seg in segments)

        log.info("STT result: '{}'", text)

        return text

    finally:
        try:
            os.remove(wav_path)
        except PermissionError:
            pass


# ─────────────────────────────────────────────────────────────────────────

def _write_wav(path: str, audio: np.ndarray, sr: int) -> None:
    """Write float32 numpy array to a 16-bit WAV file."""
    audio = audio / np.max(np.abs(audio) + 1e-6)
    audio_int16 = (audio * 32767).astype(np.int16)

    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(audio_int16.tobytes())