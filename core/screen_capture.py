import mss
from PIL import Image
from datetime import datetime

def capture_screen(region=None):
    with mss.mss() as sct:

        if region:
            monitor = {
                "top": region[1],
                "left": region[0],
                "width": region[2] - region[0],
                "height": region[3] - region[1]
            }
        else:
            monitor = sct.monitors[1]

        screenshot = sct.grab(monitor)

        img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"assets/screenshot_{timestamp}.png"

        img.save(filename)

    return filename