"""
Voice Controller
================
Manages the push-to-talk interaction loop.
Hold SPACE to record → release to send to agent → agent responds via TTS.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import threading
import time
from typing import Callable, Awaitable

from pynput import keyboard

from config import settings
from core.stt import record_audio_push_to_talk, transcribe
from core.tts import speak
from core.logger import get_logger

log = get_logger(__name__)


class VoiceController:
    """
    Push-to-talk voice controller.

    Usage::
        vc = VoiceController(on_transcript=my_async_handler)
        await vc.run()
    """

    def __init__(self, on_transcript: Callable[[str], Awaitable[str]]) -> None:
        self._on_transcript = on_transcript
        self._recording = False
        self._processing = False
        self._stop_record = threading.Event()
        self._stop_tts = threading.Event()
        self._shutdown = threading.Event()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._listener: keyboard.Listener | None = None
        self._inflight_futures: set[concurrent.futures.Future] = set()
        self._worker_threads: set[threading.Thread] = set()
        self._state_lock = threading.Lock()
        self._ptt_key = self._resolve_key(settings.audio.push_to_talk_key)

    async def run(self) -> None:
        """Start listening. Blocks until shutdown."""
        self._loop = asyncio.get_running_loop()

        log.info(
            "🎤 Voice controller ready — hold [{}] to talk, Ctrl+C to quit",
            settings.audio.push_to_talk_key,
        )

        self._listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
        )
        self._listener.start()

        try:
            # Keep alive until shutdown
            while not self._shutdown.is_set():
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            self.stop()
            raise
        finally:
            self.stop()
            self._wait_for_workers(timeout_secs=2.5)

    def stop(self) -> None:
        self._shutdown.set()
        self._recording = False
        self._stop_record.set()
        self._stop_tts.set()

        if self._listener is not None:
            self._listener.stop()
            self._listener = None

        with self._state_lock:
            futures = list(self._inflight_futures)
        for fut in futures:
            fut.cancel()

    # ── Keyboard callbacks ───────────────────────────────────────────────

    def _on_press(self, key) -> None:
        if (
            self._shutdown.is_set()
            or not self._key_matches(key)
            or self._recording
            or self._processing
        ):
            return

        self._recording = True
        self._stop_record.clear()
        # Interrupt any ongoing TTS
        self._stop_tts.set()

        t = threading.Thread(target=self._record_thread, daemon=True)
        with self._state_lock:
            self._worker_threads.add(t)
        t.start()

    def _on_release(self, key) -> None:
        if self._key_matches(key) and self._recording:
            self._recording = False
            self._stop_record.set()

    # ── Recording + processing thread ────────────────────────────────────

    def _record_thread(self) -> None:
        """Record → transcribe → process (runs on background thread)."""
        self._processing = True
        future: concurrent.futures.Future | None = None
        try:
            if self._shutdown.is_set():
                return

            audio = record_audio_push_to_talk(self._stop_record)
            if audio.size == 0:
                log.debug("Empty recording, skipping")
                return

            text = transcribe(audio)
            if not text.strip():
                log.debug("Empty transcription, skipping")
                return

            log.info("🗣  You said: '{}'", text)

            # Schedule async handler on the event loop
            loop = self._loop
            if loop is None or loop.is_closed():
                log.debug("Event loop unavailable, dropping transcript")
                return

            future = asyncio.run_coroutine_threadsafe(
                self._handle_transcript(text), loop
            )
            with self._state_lock:
                self._inflight_futures.add(future)

            # Wait for it to complete
            try:
                future.result(timeout=120)
            except concurrent.futures.CancelledError:
                if self._shutdown.is_set():
                    log.debug("Transcript task cancelled during shutdown")
                else:
                    log.warning("Transcript task cancelled")
            except concurrent.futures.TimeoutError:
                log.warning("Transcript handling timed out; cancelling task")
                future.cancel()

        except Exception:
            if self._shutdown.is_set():
                log.debug("Voice processing stopped during shutdown")
            else:
                log.exception("Error in voice processing")
        finally:
            if future is not None:
                with self._state_lock:
                    self._inflight_futures.discard(future)
            with self._state_lock:
                self._worker_threads.discard(threading.current_thread())
            self._processing = False

    async def _handle_transcript(self, text: str) -> None:
        """Process transcript through agent, then speak response."""
        if self._shutdown.is_set():
            return

        response = await self._on_transcript(text)
        if response and not self._shutdown.is_set():
            self._stop_tts.clear()
            await speak(response, stop_event=self._stop_tts)

    def _wait_for_workers(self, timeout_secs: float) -> None:
        """Best-effort worker cleanup during shutdown."""
        deadline = time.monotonic() + timeout_secs
        while time.monotonic() < deadline:
            with self._state_lock:
                alive = [t for t in self._worker_threads if t.is_alive()]
                self._worker_threads = set(alive)
            if not alive:
                return
            for t in alive:
                t.join(timeout=0.05)

    # ── Key helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _resolve_key(key_name: str):
        try:
            return getattr(keyboard.Key, key_name)
        except AttributeError:
            return keyboard.KeyCode.from_char(key_name)

    def _key_matches(self, key) -> bool:
        try:
            # Handle shift specially (left/right shift)
            if settings.audio.push_to_talk_key == "shift":
                return key in (keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r)

                return key == self._ptt_key
        except Exception:
            return False
