"""
LayerLearn — Realtime Voice Agent
==================================
Main entry point.

    python3 main.py              # Voice mode (hold SPACE to talk)
    python3 main.py --text       # Text mode (type in terminal)
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from config import settings
from core.logger import get_logger
from core.agent import Agent

log = get_logger(__name__)
console = Console()

BANNER = """[bold cyan]
 ╔════════════════════════════════════════════════════╗
 ║          🧠  LayerLearn Voice Agent  🧠           ║
 ╠════════════════════════════════════════════════════╣
 ║                                                    ║
 ║  🎤 Voice:  Hold SPACE to talk                    ║
 ║  ⌨️  Text:   python3 main.py --text                ║
 ║  ❌ Quit:   Ctrl+C                                ║
 ║                                                    ║
 ╠════════════════════════════════════════════════════╣
 ║  What I can do:                                    ║
 ║                                                    ║
 ║  👁  "what's on my screen" — see everything        ║
 ║  🔧 "help me with this code" — debug & fix        ║
 ║  🚀 "open safari" / "open spotify"                ║
 ║  🔍 "search for python tutorials"                 ║
 ║  📝 "type hello world" — automate typing          ║
 ║  ⌨️  "press cmd+s" — keyboard shortcuts           ║
 ║  📁 "read file main.py" / "write file"            ║
 ║  🕐 "what time is it"                             ║
 ║  📧 "draft an email to ..."                       ║
 ║  🔄 "reset" — clear conversation memory           ║
 ║                                                    ║
 ╚════════════════════════════════════════════════════╝
[/bold cyan]"""


# ── Text Mode ────────────────────────────────────────────────────────────

async def run_text_mode(agent: Agent) -> None:

    

    while True:
        try:
            user_input = await asyncio.to_thread(input, "Text > ")
            user_input = user_input.strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not user_input:
            continue
        if user_input.lower() in {"quit", "exit", "q"}:
            break
        if user_input.lower() == "reset":
            agent.reset()
            console.print("[yellow]Memory cleared ✓[/yellow]\n")
            continue
        console.print("[dim]Thinking…[/dim]")
        try:
            response = await agent.process(user_input)
        except Exception as e:
            response = f"Error: {e}"
            log.exception("Agent error")

        console.print()
        console.print(Panel(
            Markdown(response),
            title="🧠 [bold cyan]LayerLearn[/bold cyan]",
            border_style="cyan",
            padding=(1, 2),
        ))
        console.print()


# ── Voice Mode ───────────────────────────────────────────────────────────

async def run_voice_mode(agent: Agent) -> None:
    from core.voice_controller import VoiceController
    from core.tts import speak

    
    # Announce ready
    await speak("LayerLearn is ready. Hold shift to talk to me.")

    async def on_transcript(text: str) -> str:
        console.print(f"\n[bold green]You:[/bold green] {text}")

        if text.strip().lower() in {"reset", "clear", "start over"}:
            agent.reset()
            console.print("[yellow]Memory cleared ✓[/yellow]")
            return "Memory cleared. What would you like to do?"

        console.print("[dim]Thinking…[/dim]")
        try:
            response = await agent.process(text)
        except Exception as e:
            response = f"Sorry, something went wrong: {e}"
            log.exception("Agent error")

        console.print()
        console.print(Panel(
            Markdown(response),
            title="🧠 [bold cyan]LayerLearn[/bold cyan]",
            border_style="cyan",
            padding=(1, 2),
        ))
        console.print()
        return response

    vc = VoiceController(on_transcript=on_transcript)
    try:
        await vc.run()
    except asyncio.CancelledError:
        vc.stop()
        raise
    except KeyboardInterrupt:
        vc.stop()
    finally:
        vc.stop()


# ── Main ─────────────────────────────────────────────────────────────────

def main() -> None:
    console.print(BANNER)
    console.print("[dim]Initialising agent…[/dim]")

    agent = Agent()

    console.print("[green]Ready![/green]")
    console.print("🎤 Hold SHIFT to talk | Text > type commands\n")

    async def run_both():
        await asyncio.gather(
            run_voice_mode(agent),
            run_text_mode(agent)
        )

    try:
        asyncio.run(run_both())
    except KeyboardInterrupt:
        console.print("\n[yellow]Goodbye! 👋[/yellow]")
        sys.exit(0)

if __name__ == "__main__":
    main()
