"""
Agent Orchestrator — Human-Like Reasoning
============================================
Thinks before acting: checks if apps exist, asks follow-up questions,
remembers preferences, resolves ambiguity, reasons through multi-step tasks.

Key features:
- Smart resolver: checks installed apps, web services, asks clarifications
- Clarification flow: can ask "do you want web or app?" and handle response
- Preference memory: remembers default browser, past choices
- Intent detection: instant for known patterns
- Streaming Ollama with massive training prompt
- Safety confirmations for all destructive actions
"""

from __future__ import annotations

import json
import re
from typing import Optional

import ollama
import google.generativeai as genai

from config import settings
from core.logger import get_logger
from core.memory import AgentMemory
from core.context_memory import ContextMemory
from core.tools import all_tools, get_tool, tool_schemas
from core.safety import (
    requires_confirmation,
    format_confirmation_prompt,
    parse_confirmation,
    log_audit,
)
from core.smart_resolver import (
    resolve_open_request,
    is_app_installed,
    get_installed_browsers,
    get_pref,
    set_pref,
    WEB_SERVICES,
    ResolveResult,
)
from core.platform_utils import open_url_in_browser

log = get_logger(__name__)

# ── System Prompt — loaded from brain.py ─────────────────────────────────

from core.brain import build_full_system_prompt


# ── Abbreviation Expansion ─────────────────────────────────────────────

ABBREVIATIONS = {
    "yt": "youtube", "fb": "facebook", "ig": "instagram", "insta": "instagram",
    "tw": "twitter", "wp": "whatsapp", "wa": "whatsapp", "whtasapp": "whatsapp",
    "whatsaap": "whatsapp", "watsapp": "whatsapp",
    "li": "linkedin", "gh": "github", "so": "stack overflow",
    "gpt": "chatgpt", "vs": "vscode", "vsc": "vscode",
    "calc": "calculator", "cal": "calendar", "msg": "messages",
    "msgs": "messages", "ss": "screenshot",
}


def _expand_abbreviations(text: str) -> str:
    """Expand common abbreviations and fix typos."""
    words = text.lower().split()
    expanded = []
    for w in words:
        expanded.append(ABBREVIATIONS.get(w, w))
    return " ".join(expanded)


def _looks_like_url(text: str) -> bool:
    text = text.lower().strip()
    return ("." in text and " " not in text) or text.startswith(("http://", "https://", "www."))


# ── Intent Detection ─────────────────────────────────────────────────────

def detect_intent(text: str) -> Optional[dict]:
    """
    Fast intent detection with abbreviation expansion and smart resolution.
    """
    t = text.strip()
    tl = _expand_abbreviations(t)  # expand abbreviations + typos

    # ── Screen ───────────────────────────────────────────────────────
    if re.search(
        r"\b(what'?s on (my |the )?screen|look at (my |the )?screen|look at (this|that)|"
        r"see (my |the )?screen|can you see (this|that)|show me (my |the )?screen|screenshot)\b",
        tl,
    ):
        return {"tool": "capture_screen", "args": {}}

    if re.search(r"\b(read (my |the )?screen|what does (it|this|that|the screen) say)\b", tl):
        return {"tool": "read_screen_text", "args": {}}

    if re.search(
        r"\b(problem|error|bug|issue|exception|traceback|stack trace)\b.*\b(screen|this|that|here)\b"
        r"|\b(screen|this|that|here)\b.*\b(problem|error|bug|issue|exception|traceback|stack trace)\b",
        tl,
    ):
        return {"tool": "analyze_code", "args": {"instruction": t}}

    if re.search(r"\b(help me|fix this|debug this|what'?s wrong)\b.*\b(screen|this|that|code|here)\b", tl):
        return {"tool": "analyze_code", "args": {"instruction": t}}

    if re.search(r"\b(this|that)\s+(problem|error|bug|issue|question)\b", tl):
        return {"tool": "analyze_code", "args": {"instruction": t}}

    # ── Time ─────────────────────────────────────────────────────────
    if re.search(r"\b(what time|what'?s the time|current time|what date|what day)\b", tl):
        return {"tool": "get_time", "args": {}}

    # ── Volume ───────────────────────────────────────────────────────
    m = re.search(r"\b(?:set |change )?volume\s+(?:to\s+)?(\d+)", tl)
    if m:
        return {"tool": "set_volume", "args": {"level": int(m.group(1))}}
    if re.search(r"\bmute\b", tl):
        return {"tool": "set_volume", "args": {"level": 0}}

    # ── Calculator ───────────────────────────────────────────────────
    m = re.match(r"(?:calculate|calc|what is|what's|compute|eval)\s+([\d\s+\-*/().^%]+)", tl)
    if m:
        return {"tool": "calculator", "args": {"expression": m.group(1).strip()}}

    # ── System Info ──────────────────────────────────────────────────
    if re.search(r"\b(system info|battery|how much ram|cpu usage|disk space|memory usage)\b", tl):
        return {"tool": "system_info", "args": {}}

    # ── Dark Mode ────────────────────────────────────────────────────
    if re.search(r"\b(dark mode|light mode|toggle dark|toggle light)\b", tl):
        return {"tool": "toggle_dark_mode", "args": {}}

    # ── Running Apps ─────────────────────────────────────────────────
    if re.search(r"\b(running apps|what apps|what'?s running|show apps|what'?s open)\b", tl):
        return {"tool": "list_running_apps", "args": {}}

    # ── Active Window ────────────────────────────────────────────────
    if re.search(r"\b(active window|active app|current app|what app am i|which app|focused app)\b", tl):
        return {"tool": "active_window", "args": {}}

    # ── Minimize / Show Desktop ──────────────────────────────────────
    if re.search(r"\b(show desktop|minimize|minimise|clear screen|hide all)\b", tl):
        return {"tool": "minimize_windows", "args": {}}

    # ── Switch App ───────────────────────────────────────────────────
    m = re.match(r"(?:switch to|go to|bring up|focus|activate)\s+(.+?)\s*$", tl)
    if m:
        target = m.group(1).strip()
        if target not in ("it", "that", "this"):
            return {"tool": "switch_to_app", "args": {"name": target}}

    # ── Quit App ─────────────────────────────────────────────────────
    m = re.match(r"(?:quit|close|kill|exit|stop)\s+(.+?)\s*$", tl)
    if m:
        target = m.group(1).strip()
        if target not in ("it", "that", "this", "everything"):
            return {"tool": "quit_app", "args": {"name": target}}

    # ── Automation: Solve on screen ─────────────────────────────
    if re.search(
        r"\b(solve (this|it|the|that)( problem| question| leetcode| challenge)?|code (this|it) (for me|on screen)|write the (solution|answer|code)|solve (this )?on (my )?screen)\b",
        tl,
    ):
        lang = "python"  # default
        m = re.search(r"\b(in |using )(python|java|cpp|c\+\+|javascript|js|go|rust|typescript)\b", tl)
        if m:
            lang = m.group(2)
        return {"tool": "solve_on_screen", "args": {"instruction": t, "language": lang}}

    # ── Automation: Compose email ───────────────────────────────
    m = re.search(
        r"(?:write|compose|draft|send|type)\s+(?:an? )?(?:email|mail|message)\s+(?:to\s+)?(\S+)(?:\s+(?:about|regarding|for|on)\s+(.+))?",
        tl,
    )
    if m:
        to = m.group(1) or ""
        subject = m.group(2) or ""
        return {"tool": "compose_email", "args": {"to": to, "subject": subject, "body": subject}}

    # ── Automation: General automate ─────────────────────────────
    if re.search(
        r"\b(do (this|it|that) (for me|on screen)|automate (this|it|that)|fill (this|it|that) (out|in)|write (this|it|that) (for me|on screen)|complete (this|it|that))\b",
        tl,
    ):
        return {"tool": "automate_task", "args": {"instruction": t}}

    # ── Search web ───────────────────────────────────────────────────
    m = re.match(r"(?:search|google|look up)\s+(?:for\s+|about\s+)?(.+)", tl)
    if m:
        query = m.group(1).strip()
        if not re.match(r"(my |the |a |this )", query):
            return {"tool": "search_web", "args": {"query": query}}

    # ── "Open" commands → smart resolver ─────────────────────────────
    m = re.match(r"(?:open|go to|visit|launch)\s+(.+?)\s+(?:in|on|using|with)\s+(.+)", tl)
    if m:
        target = m.group(1).strip()
        browser = m.group(2).strip()
        url = WEB_SERVICES.get(target, target)
        if not _looks_like_url(url) and "." not in url:
            url = url + ".com"
        return {
            "tool": "open_url",
            "args": {"url": url},
            "_browser_hint": browser,
            "_smart": True,
        }

    m = re.match(r"(?:open|go to|visit|launch|start)\s+(.+?)(?:\s+app)?\s*$", tl)
    if m:
        target = m.group(1).strip()
        return {"_smart_open": target}

    return None


# ── Agent ────────────────────────────────────────────────────────────────

class Agent:
    """
    Human-like AI agent with smart reasoning, clarification, and tool calling.
    """

    def __init__(self) -> None:
        self.memory = AgentMemory()
        self.context = ContextMemory()
        self._system_prompt = build_full_system_prompt()
        self._pending_confirmation: Optional[dict] = None
        self._pending_clarification: Optional[dict] = None
        self._warmup()

    def _warmup(self) -> None:
        """Keep models loaded for faster responses (parallel warm)."""
        import threading

        def warm(model, label):
            try:
                ollama.chat(
                    model=model,
                    messages=[{"role": "user", "content": "hi"}],
                    options={"num_predict": 1},
                    keep_alive=settings.llm.keep_alive,
                )
                log.info("✓ {} model warm", label)
            except Exception as e:
                log.warning("Could not warm {} model: {}", label, e)

        for model, label in [
            (settings.llm.text_model, "Text"),
            (settings.llm.vision_model, "Vision"),
        ]:
            t = threading.Thread(target=warm, args=(model, label), daemon=True)
            t.start()

    # ── Public API ───────────────────────────────────────────────────────

    async def process(self, user_text: str) -> str:
        """Process user input → return response. Handles all flows."""

        # ── Pending confirmation (safety) ────────────────────────────
        if self._pending_confirmation:
            return self._handle_confirmation(user_text)

        # ── Pending clarification (smart questions) ──────────────────
        if self._pending_clarification:
            return self._handle_clarification(user_text)

        self.memory.add_user(user_text)

        # ── Follow-up: use cached screen context ─────────────────────
        tl = user_text.strip().lower()
        if self.context.last_screen and re.search(
            r'\b(explain that|what was that|the error|the code|you (just )?saw|you (just )?see|that (error|code|bug|issue|screen))\b',
            tl,
        ):
            ctx = self.context.last_screen
            self.memory.add_user(
                f"[Context: you recently analyzed the screen and saw: {ctx.description[:500]}]\n"
                f"User follow-up: {user_text}"
            )
            return self._process_with_llm()

        # ── Fast path: Intent detection ──────────────────────────────
        intent = detect_intent(user_text)

        if intent:
            # Smart open (needs resolution)
            if "_smart_open" in intent:
                return self._smart_open(intent["_smart_open"])

            # Open with specific browser
            if intent.get("_smart"):
                browser_hint = intent.pop("_browser_hint", "")
                intent.pop("_smart", None)
                if browser_hint:
                    browser_name = self._resolve_browser_name(browser_hint)
                    if browser_name:
                        set_pref("default_browser", browser_name)
                return self._handle_tool_call(intent)

            # Normal tool call
            return self._handle_tool_call(intent)

        # ── Normal path: Ask the LLM ────────────────────────────────
        reply = self._call_llm(self.memory.to_messages())
        if reply is None:
            err = "Sorry, I couldn't process that."
            self.memory.add_assistant(err)
            return err

        # Check for tool call in LLM response
        tool_call = self._extract_tool_call(reply)
        if tool_call:
            return self._handle_tool_call(tool_call)

        self.memory.add_assistant(reply)
        return reply

    def reset(self) -> None:
        self.memory.clear()
        self.context.clear()
        self._pending_confirmation = None
        self._pending_clarification = None
        log.info("Agent reset")

    # ── Smart Open (Decisive — never asks, just acts) ──────────────────────

    def _smart_open(self, target: str) -> str:
        """
        Resolve "open X" — never asks questions, always takes action.
        Prefers native apps, falls back to web, auto-searches if unknown.
        """
        result = resolve_open_request(target)
        log.info("🧠 Smart resolve '{}' → {} ({})", target, result.action, result.target)

        if result.action == "open_app":
            tool_result = self._handle_tool_call({
                "tool": "open_app",
                "args": {"name": result.target},
            })
            # Use the friendly message from resolver, not the tool's verbose output
            if result.message:
                self.memory.add_assistant(result.message)
                return result.message
            return tool_result

        elif result.action == "open_url":
            return self._open_in_browser(result.target, result.browser, result.message)

        # Fallback (shouldn't happen but just in case)
        return self._handle_tool_call({
            "tool": "open_app",
            "args": {"name": target.title()},
        })

    def _open_in_browser(self, url: str, browser: str, message: str = "") -> str:
        """Open a URL in a specific browser. Returns concise message."""
        ok, fallback_message = open_url_in_browser(url, browser)
        if ok:
            # Use the friendly message (e.g. "Opening YouTube") not the URL
            msg = message or f"Done."
            self.memory.add_assistant(msg)
            log.info("🌐 {}", msg)
            return msg

        err = f"Couldn't open that. {fallback_message}"
        self.memory.add_assistant(err)
        return err

    # ── Clarification Handling ───────────────────────────────────────────

    def _handle_clarification(self, user_response: str) -> str:
        """Handle user's response to a clarifying question."""
        pending = self._pending_clarification
        self._pending_clarification = None
        response_lower = user_response.strip().lower()

        if pending["type"] == "web_or_app":
            # User choosing between app and web
            if any(w in response_lower for w in ["app", "desktop", "native", "application"]):
                return self._handle_tool_call({
                    "tool": "open_app",
                    "args": {"name": pending["app_name"]},
                })
            elif any(w in response_lower for w in ["web", "browser", "online", "chrome", "safari"]):
                browser = get_pref("default_browser", "Google Chrome")
                # Did they mention a specific browser?
                if "chrome" in response_lower:
                    browser = "Google Chrome"
                    set_pref("default_browser", browser)
                elif "safari" in response_lower:
                    browser = "Safari"
                    set_pref("default_browser", browser)
                elif "firefox" in response_lower:
                    browser = "Firefox"
                    set_pref("default_browser", browser)
                return self._open_in_browser(pending["url"], browser)
            else:
                # Default to web
                browser = get_pref("default_browser", "Google Chrome")
                return self._open_in_browser(pending["url"], browser)

        elif pending["type"] == "not_found":
            # User responding to "not found, search web?"
            if parse_confirmation(response_lower):
                return self._handle_tool_call({
                    "tool": "search_web",
                    "args": {"query": pending["original"]},
                })
            else:
                msg = "Alright, no problem!"
                self.memory.add_assistant(msg)
                return msg

        elif pending["type"] == "choose_browser":
            browser = self._resolve_browser_name(response_lower)
            if browser:
                set_pref("default_browser", browser)
                return self._open_in_browser(pending["url"], browser)
            else:
                browser = "Google Chrome"
                return self._open_in_browser(pending["url"], browser)

        # Fallback — pass to LLM
        self.memory.add_user(user_response)
        return self._process_with_llm()

    # ── Browser Name Resolution ──────────────────────────────────────────

    def _resolve_browser_name(self, text: str) -> Optional[str]:
        """Resolve a browser name from user input."""
        text = text.lower().strip()
        browser_map = {
            "chrome": "Google Chrome",
            "google chrome": "Google Chrome",
            "safari": "Safari",
            "firefox": "Firefox",
            "brave": "Brave Browser",
            "edge": "Microsoft Edge",
            "arc": "Arc",
            "opera": "Opera",
        }
        for key, name in browser_map.items():
            if key in text:
                return name
        return None

    # ── LLM Calls ────────────────────────────────────────────────────────

    def _call_llm(self, messages: list[dict], extra_system: str = "") -> Optional[str]:
        system = self._system_prompt
        if extra_system:
            system += "\n\n" + extra_system

        full_msgs = [{"role": "system", "content": system}] + messages

        try:
            # Try Gemma first if configured
            if settings.llm.backend.lower() == "gemma" and settings.llm.google_api_key:
                return self._call_gemma(full_msgs, system)
            # Fall back to Ollama
            return self._call_ollama(full_msgs)
        except Exception as e:
            log.error("LLM failed: {}", e)
            return None

    def _call_gemma(self, full_msgs: list[dict], system: str) -> Optional[str]:
        """Call Google Gemini/Gemma API."""
        try:
            genai.configure(api_key=settings.llm.google_api_key)
            model = genai.GenerativeModel(
                settings.llm.gemma_model,
                generation_config={
                    "temperature": settings.llm.temperature,
                    "max_output_tokens": settings.llm.max_tokens,
                },
                system_instruction=system,
            )
            
            # Convert messages to Gemma format
            # Gemma expects list of Content objects, not raw dicts
            gemma_msgs = []
            for msg in full_msgs:
                if msg["role"] != "system":  # system is passed separately
                    gemma_msgs.append({
                        "role": msg["role"],
                        "parts": [{"text": msg["content"]}]
                    })
            
            response = model.generate_content(gemma_msgs)
            log.debug("✅ Gemma response: {} chars", len(response.text))
            return response.text
        except Exception as e:
            log.error("❌ Gemma call failed: {}, falling back to Ollama", e)
            return self._call_ollama([{"role": "system", "content": system}] + [m for m in full_msgs if m["role"] != "system"])

    def _call_ollama(self, full_msgs: list[dict]) -> Optional[str]:
        """Call Ollama API."""
        try:
            stream = ollama.chat(
                model=settings.llm.text_model,
                messages=full_msgs,
                stream=True,
                options={
                    "temperature": settings.llm.temperature,
                    "num_predict": settings.llm.max_tokens,
                },
                keep_alive=settings.llm.keep_alive,
            )
            return "".join(chunk["message"]["content"] for chunk in stream)
        except Exception as e:
            log.error("❌ Ollama call failed: {}", e)
            raise

    def _process_with_llm(self) -> str:
        """Standard LLM processing path."""
        reply = self._call_llm(self.memory.to_messages())
        if reply is None:
            err = "Sorry, I couldn't process that."
            self.memory.add_assistant(err)
            return err

        tool_call = self._extract_tool_call(reply)
        if tool_call:
            return self._handle_tool_call(tool_call)

        self.memory.add_assistant(reply)
        return reply

    # ── Tool Call Extraction ─────────────────────────────────────────────

    def _extract_tool_call(self, text: str) -> Optional[dict]:
        # Pattern 1: ```tool { ... } ```
        m = re.search(r"```tool\s*\n?\s*(\{.*?\})\s*\n?```", text, re.DOTALL)
        if m:
            return self._parse_json(m.group(1))

        # Pattern 2: <tool_call> ... </tool_call>
        m = re.search(r"<tool_call>\s*(\{.*?\})\s*</tool_call>", text, re.DOTALL)
        if m:
            return self._parse_json(m.group(1))

        # Pattern 3: raw JSON
        m = re.search(r'\{\s*"tool"\s*:\s*"[^"]+"\s*,\s*"args"\s*:\s*\{[^}]*\}\s*\}', text)
        if m:
            return self._parse_json(m.group(0))

        # Pattern 4: lenient
        m = re.search(r'\{[^}]*"tool"\s*:\s*"(\w+)"[^}]*\}', text)
        if m:
            return self._parse_json(m.group(0))

        return None

    def _parse_json(self, text: str) -> Optional[dict]:
        try:
            data = json.loads(text)
            if "tool" in data:
                data.setdefault("args", {})
                return data
        except json.JSONDecodeError:
            pass
        return None

    # ── Tool Execution ───────────────────────────────────────────────────

    def _handle_tool_call(self, call: dict) -> str:
        tool_name = call.get("tool", "")
        args = call.get("args", {})

        tool = get_tool(tool_name)
        if not tool:
            msg = f"I don't have a tool called '{tool_name}'."
            self.memory.add_assistant(msg)
            return msg

        if requires_confirmation(tool):
            self._pending_confirmation = {"tool_name": tool_name, "args": args}
            prompt = format_confirmation_prompt(tool_name, args)
            log.info("⚠️  Confirmation: {} {}", tool_name, args)
            self.memory.add_assistant(prompt)
            return prompt

        return self._execute_and_summarise(tool_name, args)

    def _execute_and_summarise(self, tool_name: str, args: dict) -> str:
        tool = get_tool(tool_name)
        if not tool:
            return f"Tool '{tool_name}' not found."

        log.info("▶ {} args={}", tool_name, args)

        try:
            result = tool.execute(**args)
        except Exception as e:
            err = f"Tool '{tool_name}' failed: {e}"
            log.error(err)
            self.memory.add_assistant(err)
            return err

        self.memory.add_tool(tool_name, result.output)
        self.context.record_tool(tool_name)

        # Cache screen analysis for follow-up questions
        screen_tools = {"capture_screen", "screen_question", "analyze_code",
                        "generate_code", "read_screen_text"}
        if tool_name in screen_tools and result.success:
            from core.vision import _get_active_app
            self.context.store_screen(result.output, _get_active_app())

        if not result.success:
            self.memory.add_assistant(result.output)
            return result.output

        # ── Direct-return tools (NO LLM re-summarization) ────────────
        direct = {
            "capture_screen", "screen_question", "analyze_code",
            "generate_code", "read_screen_text",
            "open_app", "open_url", "open_website_in_chrome", "search_web",
            "get_time", "set_volume", "send_notification",
            "copy_to_clipboard", "git_status", "git_diff", "read_clipboard",
            "calculator", "system_info", "active_window",
            "toggle_dark_mode", "do_not_disturb", "list_running_apps",
            "quit_app", "minimize_windows", "switch_to_app",
            "set_brightness", "word_count",
            "sleep_mac", "lock_screen", "empty_trash",
            # Automation tools
            "solve_on_screen", "compose_email", "automate_task",
        }
        if tool_name in direct:
            output = result.output
            if len(output) > 500:
                output = output[:500] + "..."
            self.memory.add_assistant(output)
            return output

        # ── Complex tools — LLM summary for voice ────────────────────
        summary = self._call_llm(
            self.memory.to_messages() + [{
                "role": "user",
                "content": (
                    f"Summarise this `{tool_name}` result for voice (1-2 sentences). "
                    f"Be concise. NO tool calls:\n{result.output[:2000]}"
                ),
            }],
            extra_system="Summarise in 1-2 sentences. NO tool calls.",
        )

        if summary is None:
            summary = result.output[:300]

        # Strip accidental tool calls
        summary = re.sub(r"```tool[\s\S]*?```", "", summary)
        summary = re.sub(r"<tool_call>[\s\S]*?</tool_call>", "", summary)
        summary = summary.strip() or result.output[:300]

        self.memory.add_assistant(summary)
        return summary

    # ── Confirmation ─────────────────────────────────────────────────────

    def _handle_confirmation(self, user_response: str) -> str:
        pending = self._pending_confirmation
        self._pending_confirmation = None

        confirmed = parse_confirmation(user_response)
        log_audit(pending["tool_name"], pending["args"], confirmed, user_response)

        if confirmed:
            return self._execute_and_summarise(pending["tool_name"], pending["args"])
        else:
            msg = f"Cancelled {pending['tool_name']}."
            self.memory.add_assistant(msg)
            return msg
