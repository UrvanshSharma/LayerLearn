import keyboard

def start_hotkey_listener(callback):
    print("Listening for Ctrl + Shift + A...")

    keyboard.add_hotkey("ctrl+shift+a", callback)

    keyboard.wait()