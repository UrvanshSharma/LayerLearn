"""
Structured logging for LayerLearn.
Uses loguru for coloured console + JSON file output.
"""

import sys
from loguru import logger
from config import settings, LOGS_DIR

# ── Remove default handler ──────────────────────────────────────────────
logger.remove()

# ── Console handler (human-friendly) ────────────────────────────────────
_console_fmt = (
    "<green>{time:HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> — "
    "<level>{message}</level>"
)
logger.add(
    sys.stderr,
    format=_console_fmt,
    level="DEBUG" if settings.debug else "INFO",
    colorize=True,
)

# ── File handler (structured JSON, rotated) ─────────────────────────────
logger.add(
    LOGS_DIR / "layerlearn_{time:YYYY-MM-DD}.log",
    format="{time:YYYY-MM-DDTHH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} — {message}",
    level="DEBUG",
    rotation="10 MB",
    retention="7 days",
    compression="gz",
)


def get_logger(name: str):
    """Return a contextualised logger for the given module name."""
    return logger.bind(module=name)
