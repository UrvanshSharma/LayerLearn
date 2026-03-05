
import tkinter as tk
from tkinter import ttk
import threading
import asyncio
import traceback


# ───────────── Splash Screen ─────────────

class SplashScreen:

    def __init__(self):

        self.root = tk.Tk()
        self.root.title("LayerLearn")
        self.root.geometry("500x300")
        self.root.resizable(False, False)

        container = tk.Frame(self.root)
        container.pack(expand=True)

        title = tk.Label(
            container,
            text="🧠 LayerLearn",
            font=("Segoe UI", 20, "bold")
        )
        title.pack(pady=(0, 10))

        self.status = tk.Label(
            container,
            text="Starting...",
            font=("Segoe UI", 11)
        )
        self.status.pack(pady=(0, 15))

        self.progress = ttk.Progressbar(
            container,
            orient="horizontal",
            length=260,
            mode="determinate"
        )

        self.progress.pack()

    def set_status(self, text, value):

        def update():
            self.status.config(text=text)
            self.progress["value"] = value

        self.root.after(0, update)

    def close(self):
        self.root.after(0, self.root.destroy)


# ───────────── Main GUI ─────────────

class LayerLearnGUI:

    def __init__(self, root, agent, voice_controller):

        self.root = root
        self.agent = agent
        self.voice_controller_class = voice_controller

        self.root.title("LayerLearn Voice Agent 🧠")
        self.root.geometry("650x520")
        self.root.configure(bg="#1e1e1e")

        # ───────── Chat area ─────────

        chat_frame = tk.Frame(root, bg="#1e1e1e")
        chat_frame.pack(side="top", fill="both", expand=True, padx=10, pady=(10, 0))

        self.text = tk.Text(
            chat_frame,
            bg="#121212",
            fg="#e6e6e6",
            insertbackground="white",
            wrap="word",
            font=("Segoe UI", 10),
            relief="flat",
            padx=10,
            pady=10
        )

        self.text.pack(fill="both", expand=True)

        # message colors
        self.text.tag_config("user", foreground="#4ea1ff")
        self.text.tag_config("ai", foreground="#7cffb2")
        self.text.tag_config("system", foreground="#aaaaaa")
        self.text.tag_config("thinking", foreground="#ffaa33")

        self.text.config(state="disabled")

        # ───────── Input bar ─────────

        input_frame = tk.Frame(root, bg="#1e1e1e", height=60)
        input_frame.pack(side="bottom", fill="x", padx=10, pady=10)
        input_frame.pack_propagate(False)

        self.entry = tk.Entry(
            input_frame,
            bg="#2a2a2a",
            fg="white",
            insertbackground="white",
            relief="flat",
            font=("Segoe UI", 10)
        )

        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 10), ipady=8)

        send_btn = tk.Button(
            input_frame,
            text="Send",
            bg="#3a7afe",
            fg="white",
            relief="flat",
            command=self.send
        )

        send_btn.pack(side="right")

        self.entry.bind("<Return>", self.send)

        # placeholder text
        self.entry.insert(0, "Type a message...")
        self.entry.bind("<FocusIn>", self.clear_placeholder)
        self.entry.bind("<FocusOut>", self.restore_placeholder)

        self.add_message("System", "LayerLearn ready.", "system")

        threading.Thread(target=self.start_voice, daemon=True).start()

    # ───────── placeholder helpers ─────────

    def clear_placeholder(self, event):

        if self.entry.get() == "Type a message...":
            self.entry.delete(0, tk.END)

    def restore_placeholder(self, event):

        if not self.entry.get():
            self.entry.insert(0, "Type a message...")

    # ───────── message helper ─────────

    def add_message(self, label, msg, tag):

        self.text.config(state="normal")
        self.text.insert("end", f"\n{label}: {msg}\n", tag)
        self.text.config(state="disabled")
        self.text.see("end")

    # ───────── Text input ─────────

    def send(self, event=None):

        command = self.entry.get()

        if command.strip() == "" or command == "Type a message...":
            return

        self.entry.delete(0, tk.END)

        self.add_message("You", command, "user")

        threading.Thread(
            target=self.run_agent,
            args=(command,),
            daemon=True
        ).start()

    def run_agent(self, command):

        async def process():

            self.add_message("🧠", "Thinking...", "thinking")

            try:
                response = await self.agent.process(command)
            except Exception as e:
                response = f"Error: {e}"
                traceback.print_exc()

            self.add_message("AI", response, "ai")

        asyncio.run(process())

    # ───────── Voice system ─────────

    def start_voice(self):

        async def voice_loop():

            async def on_transcript(text):

                self.add_message("🎤 You", text, "user")

                self.add_message("🧠", "Thinking...", "thinking")

                try:
                    response = await self.agent.process(text)
                except Exception as e:
                    response = f"Error: {e}"
                    traceback.print_exc()

                self.add_message("AI", response, "ai")

                return response

            self.voice_controller = self.voice_controller_class(
                on_transcript=on_transcript
            )

            await self.voice_controller.run()

        try:
            asyncio.run(voice_loop())
        except Exception:
            traceback.print_exc()
            self.add_message("System", "Voice system stopped unexpectedly.", "system")


# ───────── Startup Loader ─────────

def load_system(splash):

    splash.set_status("Loading agent...", 20)

    from core.agent import Agent

    splash.set_status("Loading voice system...", 40)

    from core.voice_controller import VoiceController

    splash.set_status("Loading Whisper model...", 60)

    from core.stt import _get_model
    _get_model()

    splash.set_status("Initialising AI agent...", 80)

    agent = Agent()

    splash.set_status("Warming AI models...", 90)

    asyncio.run(agent.process("hello"))

    splash.set_status("Ready!", 100)

    splash.close()

    return agent, VoiceController


# ───────── Main Entry ─────────

if __name__ == "__main__":

    splash = SplashScreen()

    result = {}

    def background_load():
        agent, vc = load_system(splash)
        result["agent"] = agent
        result["vc"] = vc

    loader = threading.Thread(target=background_load)
    loader.start()

    splash.root.mainloop()

    loader.join()

    root = tk.Tk()

    app = LayerLearnGUI(root, result["agent"], result["vc"])

    root.mainloop()

