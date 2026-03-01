import tkinter as tk

def select_area():
    coords = []
    cancelled = {"value": False}
    rect = None

    def on_mouse_down(event):
        coords.clear()
        coords.extend([event.x_root, event.y_root])
        nonlocal rect
        rect = canvas.create_rectangle(event.x, event.y, event.x, event.y, outline="red", width=2)

    def on_mouse_move(event):
        if rect:
            canvas.coords(rect, coords[0]-root.winfo_rootx(), coords[1]-root.winfo_rooty(), event.x, event.y)

    def on_mouse_up(event):
        coords.extend([event.x_root, event.y_root])
        root.quit()

    def on_escape(event):
        cancelled["value"] = True
        root.quit()

    root = tk.Tk()
    root.attributes("-fullscreen", True)
    root.attributes("-alpha", 0.3)
    root.attributes("-topmost", True)
    root.configure(bg="black")

    canvas = tk.Canvas(root, cursor="cross", bg="black")
    canvas.pack(fill=tk.BOTH, expand=True)

    canvas.bind("<ButtonPress-1>", on_mouse_down)
    canvas.bind("<B1-Motion>", on_mouse_move)  # 👈 LIVE BOX
    canvas.bind("<ButtonRelease-1>", on_mouse_up)
    root.bind("<Escape>", on_escape)

    root.focus_force()
    root.mainloop()
    root.destroy()

    if cancelled["value"]:
        return None

    return coords