import tkinter as tk

def get_user_prompt():
    prompt = {"value": ""}

    def submit():
        prompt["value"] = entry.get()
        win.destroy()

    win = tk.Tk()
    win.title("What do you want AI to do?")
    win.attributes("-topmost", True)
    win.geometry("300x120")

    label = tk.Label(win, text="Ask AI what to do:")
    label.pack()

    entry = tk.Entry(win, width=40)
    entry.pack()

    btn = tk.Button(win, text="Submit", command=submit)
    btn.pack()

    win.mainloop()

    return prompt["value"]