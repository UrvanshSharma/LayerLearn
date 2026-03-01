import tkinter as tk

def show_popup(text, x=200, y=200):
    popup = tk.Tk()
    popup.title("LayerLearn")

    popup.attributes("-topmost", True)
    popup.geometry(f"400x300+{x}+{y}")

    text_box = tk.Text(popup, wrap="word")
    text_box.insert("1.0", text)
    text_box.pack(expand=True, fill="both")

    close_btn = tk.Button(popup, text="Close", command=popup.destroy)
    close_btn.pack()

    popup.mainloop()