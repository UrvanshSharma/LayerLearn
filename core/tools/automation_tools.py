"""
Automation Tools — Real Task Automation
=========================================
These tools ACTUALLY DO things on screen:
- Solve coding problems by typing the solution
- Compose and type emails
- Automate multi-step screen tasks
"""

from __future__ import annotations

import time
import subprocess
import platform

from core.tools import Tool, ToolResult, register_tool
from core.logger import get_logger

log = get_logger(__name__)

IS_MAC = platform.system() == "Darwin"


def _type_text_on_screen(text: str, delay: float = 0.02) -> bool:
    """Type text on screen using pyautogui (fast, cross-platform)."""
    try:
        import pyautogui
        pyautogui.PAUSE = delay
        # Use pyperclip + paste for speed and Unicode support
        import pyperclip
        pyperclip.copy(text)
        if IS_MAC:
            pyautogui.hotkey("command", "v")
        else:
            pyautogui.hotkey("ctrl", "v")
        time.sleep(0.1)
        return True
    except Exception as e:
        log.error("Failed to type on screen: {}", e)
        return False


def _select_all() -> None:
    """Select all text in current field."""
    import pyautogui
    if IS_MAC:
        pyautogui.hotkey("command", "a")
    else:
        pyautogui.hotkey("ctrl", "a")
    time.sleep(0.1)


def _click_center() -> None:
    """Click center of screen to ensure focus."""
    import pyautogui
    w, h = pyautogui.size()
    pyautogui.click(w // 2, h // 2)
    time.sleep(0.2)


# ── Solve on Screen Tool ─────────────────────────────────────────────────

class SolveOnScreenTool(Tool):
    name = "solve_on_screen"
    description = (
        "Look at a coding problem on screen (LeetCode, HackerRank, etc), "
        "understand it, generate the solution, and TYPE it directly into the "
        "code editor on the platform. Use for: 'solve this', 'code this for me', "
        "'solve this leetcode', 'write the solution'."
    )
    requires_confirmation = True  # Always confirm before typing!

    def execute(self, **kwargs) -> ToolResult:
        instruction = kwargs.get("instruction", "Solve this coding problem")
        language = kwargs.get("language", "python")

        try:
            # Step 1: Capture and understand the problem
            from core.vision import analyze_image
            from core.screen_capture import capture_screen

            log.info("🧠 Step 1: Reading the problem from screen...")
            img, _ = capture_screen()
            problem_desc = analyze_image(
                img,
                prompt=(
                    "Read this coding problem carefully. Extract:\n"
                    "1. Problem title/name\n"
                    "2. Full problem description\n"
                    "3. Input/output format\n"
                    "4. Constraints\n"
                    "5. Example test cases\n"
                    "Be precise and exact. Quote any code or text exactly as shown."
                ),
            )

            # Step 2: Generate the solution
            log.info("🧠 Step 2: Generating solution...")
            import ollama
            from config import settings

            solution_response = ollama.chat(
                model=settings.llm.text_model,
                messages=[{
                    "role": "user",
                    "content": (
                        f"You are an expert competitive programmer.\n\n"
                        f"PROBLEM FROM SCREEN:\n{problem_desc}\n\n"
                        f"TASK: Write a COMPLETE, OPTIMAL solution in {language}.\n\n"
                        f"RULES:\n"
                        f"1. Output ONLY the code — no explanations, no comments about approach\n"
                        f"2. Include ALL necessary imports\n"
                        f"3. Use the exact class/function signature shown in the problem\n"
                        f"4. Handle all edge cases\n"
                        f"5. Optimize for time and space complexity\n"
                        f"6. Do NOT wrap in markdown code blocks — output RAW code only\n"
                        f"7. Do NOT include any text before or after the code\n\n"
                        f"OUTPUT THE SOLUTION CODE NOW:"
                    ),
                }],
                options={"temperature": 0.1, "num_predict": 2048},
            )

            code = solution_response.message.content.strip()

            # Clean code — remove any markdown fencing
            if code.startswith("```"):
                lines = code.split("\n")
                # Remove first and last ``` lines
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                code = "\n".join(lines)

            # Step 3: Type it on screen
            log.info("⌨️ Step 3: Typing solution on screen...")

            # Select all existing code first (to replace)
            _select_all()
            time.sleep(0.2)

            # Type the solution
            if _type_text_on_screen(code):
                return ToolResult(
                    success=True,
                    output=f"Done! I solved the problem and typed the solution on screen. "
                           f"({len(code)} chars, {language}). Check it and submit!",
                )
            else:
                return ToolResult(
                    success=False,
                    output=f"Generated the solution but couldn't type it. Here it is:\n{code}",
                )

        except Exception as e:
            return ToolResult(success=False, output=f"Automation failed: {e}")


# ── Compose Email Tool ───────────────────────────────────────────────────

class ComposeEmailTool(Tool):
    name = "compose_email"
    description = (
        "Compose an email and TYPE it directly into the email compose window. "
        "Opens Gmail/Mail if needed. Use for: 'write an email to...', "
        "'send email to...', 'email john about...', 'compose a mail'."
    )
    requires_confirmation = True

    def execute(self, **kwargs) -> ToolResult:
        to = kwargs.get("to", "")
        subject = kwargs.get("subject", "")
        body = kwargs.get("body", "")
        tone = kwargs.get("tone", "professional")

        try:
            # If we have basic info, generate the email
            import ollama
            from config import settings

            if not body and not subject:
                # Need more context — look at screen for draft
                from core.vision import analyze_image
                from core.screen_capture import capture_screen
                img, _ = capture_screen()
                context = analyze_image(
                    img,
                    prompt="Read any email draft or compose window on screen. What's the context?",
                )
                prompt_context = f"Context from screen: {context}"
            else:
                prompt_context = f"Subject: {subject}\nBody notes: {body}"

            response = ollama.chat(
                model=settings.llm.text_model,
                messages=[{
                    "role": "user",
                    "content": (
                        f"Write a {tone} email.\n"
                        f"To: {to}\n"
                        f"{prompt_context}\n\n"
                        f"RULES:\n"
                        f"1. Write ONLY the email body — no subject line, no 'Subject:' prefix\n"
                        f"2. Be {tone} but natural\n"
                        f"3. Keep it concise and clear\n"
                        f"4. Include a proper greeting and sign-off\n"
                        f"5. Output ONLY the email text, nothing else\n"
                    ),
                }],
                options={"temperature": 0.3, "num_predict": 1024},
            )

            email_text = response.message.content.strip()

            # Type it on screen
            if _type_text_on_screen(email_text):
                return ToolResult(
                    success=True,
                    output=f"Email composed and typed on screen. Review it and hit send!",
                )
            else:
                return ToolResult(
                    success=False,
                    output=f"Generated the email but couldn't type it:\n{email_text}",
                )

        except Exception as e:
            return ToolResult(success=False, output=f"Email automation failed: {e}")


# ── Automate Task Tool ───────────────────────────────────────────────────

class AutomateTaskTool(Tool):
    name = "automate_task"
    description = (
        "Look at the screen and automate whatever task is visible. "
        "Understands forms, text fields, code editors, etc. "
        "Types content, fills forms, interacts with UI. "
        "Use for: 'do this for me', 'fill this out', 'automate this', "
        "'write this for me', 'complete this'."
    )
    requires_confirmation = True

    def execute(self, **kwargs) -> ToolResult:
        instruction = kwargs.get("instruction", "Automate what's on screen")

        try:
            from core.vision import analyze_image
            from core.screen_capture import capture_screen
            import ollama
            from config import settings

            # Step 1: Understand context
            log.info("🧠 Analyzing screen for automation...")
            img, _ = capture_screen()
            screen_context = analyze_image(
                img,
                prompt=(
                    "Analyze this screen for task automation.\n"
                    "1. What app is open?\n"
                    "2. What is the user trying to do?\n"
                    "3. Are there any text fields, code editors, or forms visible?\n"
                    "4. What content needs to be written or filled in?\n"
                    "5. What's the current state (empty, partially filled, etc.)?\n"
                    "Be precise and exact."
                ),
            )

            # Step 2: Generate content
            log.info("🧠 Generating content for automation...")
            response = ollama.chat(
                model=settings.llm.text_model,
                messages=[{
                    "role": "user",
                    "content": (
                        f"SCREEN CONTEXT:\n{screen_context}\n\n"
                        f"USER INSTRUCTION: {instruction}\n\n"
                        f"Generate ONLY the text/code that should be typed on screen.\n"
                        f"RULES:\n"
                        f"1. Output ONLY the content to type — no explanations\n"
                        f"2. Match the format expected (code, email, form data, etc)\n"
                        f"3. Be accurate and complete\n"
                        f"4. Do NOT wrap in markdown code blocks\n"
                    ),
                }],
                options={"temperature": 0.2, "num_predict": 2048},
            )

            content = response.message.content.strip()
            if content.startswith("```"):
                lines = content.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                content = "\n".join(lines)

            # Step 3: Type on screen
            log.info("⌨️ Typing content on screen...")
            if _type_text_on_screen(content):
                return ToolResult(
                    success=True,
                    output=f"Done! Typed the content on screen. ({len(content)} chars)",
                )
            else:
                return ToolResult(
                    success=False,
                    output=f"Generated content but couldn't type it:\n{content}",
                )

        except Exception as e:
            return ToolResult(success=False, output=f"Automation failed: {e}")


# ── Register ─────────────────────────────────────────────────────────────
for _cls in [SolveOnScreenTool, ComposeEmailTool, AutomateTaskTool]:
    register_tool(_cls())
