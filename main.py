import time
from core.hotkey import start_hotkey_listener
from core.screen_capture import capture_screen
from core.ocr_reader import extract_text
from core.ai_engine import explain_text
from core.area_selector import select_area 
from ui.popup import show_popup
from ui.prompt_input import get_user_prompt

def run_assistant():
    print("Assistant Activated 🚀")

    time.sleep(0.5)

    region = select_area()

    if region is None:
        print("Selection cancelled ❌")
        return

    image_path = capture_screen(region)
    text = extract_text(image_path)

    if not text.strip():
        return

    user_prompt = get_user_prompt()

    if not user_prompt:
        user_prompt = "Explain this simply"

    explanation = explain_text(text, user_prompt)
    show_popup(explanation, region[0], region[1])

if __name__ == "__main__":
    start_hotkey_listener(run_assistant)