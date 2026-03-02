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
    console.print(BANNER)
    console.print("[bold green]Text mode active.[/bold green] Type your messages:\n")

    while True:
        try:
            user_input = input("You > ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[yellow]Goodbye! 👋[/yellow]")
            break

        if not user_input:
            continue
        if user_input.lower() in {"quit", "exit", "q"}:
            console.print("[yellow]Goodbye! 👋[/yellow]")
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

    console.print(BANNER)
    console.print(
        f"[bold green]🎤 Voice mode active.[/bold green] "
        f"Hold [bold yellow]SPACE[/bold yellow] to talk.\n"
    )

    # Announce ready
    await speak("LayerLearn is ready. Hold space to talk to me.")

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
    parser = argparse.ArgumentParser(description="LayerLearn Voice Agent")
    parser.add_argument("--text", action="store_true", help="Text mode")
    parser.add_argument("--debug", action="store_true", help="Debug logging")
    args = parser.parse_args()

    if args.debug:
        settings.debug = True

    console.print("[dim]Initialising agent…[/dim]")
    agent = Agent()
    console.print("[dim]Ready! ✓[/dim]\n")

    try:
        if args.text:
            asyncio.run(run_text_mode(agent))
        else:
            asyncio.run(run_voice_mode(agent))
    except KeyboardInterrupt:
        console.print("\n[yellow]Goodbye! 👋[/yellow]")
        sys.exit(0)


if __name__ == "__main__":
    main()
